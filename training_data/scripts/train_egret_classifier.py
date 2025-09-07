#!/usr/bin/env python3
"""
Train Stage-2 classifier for egret species identification.

This script trains an EfficientNet model to classify egret species from cropped images.
Uses transfer learning from ImageNet pre-trained weights.
"""

import argparse
import sys
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from PIL import Image
from sklearn.metrics import classification_report, confusion_matrix
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms
from tqdm import tqdm

warnings.filterwarnings("ignore")


class FilteredImageFolder(Dataset):
    """Custom dataset that filters out classes with no images."""

    def __init__(self, root, transform=None):
        self.root = Path(root)
        self.transform = transform
        self.samples = []
        self.class_to_idx = {}
        self.classes = []

        # Find classes that have images
        for class_dir in sorted(self.root.iterdir()):
            if class_dir.is_dir():
                images = list(class_dir.glob("*.png"))
                if images:  # Only include classes with images
                    class_name = class_dir.name
                    class_idx = len(self.classes)
                    self.classes.append(class_name)
                    self.class_to_idx[class_name] = class_idx

                    # Add samples
                    for img_path in images:
                        self.samples.append((str(img_path), class_idx))

        print(f"Found {len(self.classes)} classes with images: {self.classes}")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        img_path, label = self.samples[idx]
        image = Image.open(img_path).convert("RGB")

        if self.transform:
            image = self.transform(image)

        return image, label


class EgretClassifierTrainer:
    """Trainer for egret species classification."""

    def __init__(self, data_dir: str, model_name: str = "efficientnet_b0"):
        self.data_dir = Path(data_dir)
        self.model_name = model_name
        # num_classes will be determined from the dataset
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Class names
        self.class_names = ["Chinese Egret", "Great Egret", "Intermediate Egret", "Little Egret"]

        # Setup data transforms
        self.setup_transforms()

        # Load datasets
        self.load_datasets()

        # Setup model (now that we know the actual number of classes)
        self.setup_model()

        # Setup training components
        self.setup_training()

    def setup_transforms(self):
        """Setup data augmentation and preprocessing transforms."""
        self.train_transform = transforms.Compose(
            [
                transforms.Resize((224, 224)),
                transforms.RandomHorizontalFlip(p=0.5),
                transforms.RandomRotation(15),
                transforms.ColorJitter(brightness=0.1, contrast=0.1, saturation=0.1),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ]
        )

        self.val_transform = transforms.Compose(
            [
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ]
        )

    def load_datasets(self):
        """Load training and validation datasets."""
        # Load training dataset
        try:
            self.train_dataset = FilteredImageFolder(
                root=self.data_dir / "train", transform=self.train_transform
            )
        except Exception as e:
            print(f"❌ Error loading training data: {e}")
            print("Run crop extraction first.")
            raise

        # Load validation dataset (may not exist)
        val_path = self.data_dir / "val"
        if val_path.exists() and any(val_path.rglob("*.png")):
            try:
                self.val_dataset = FilteredImageFolder(root=val_path, transform=self.val_transform)
            except:
                print("⚠️ No validation data available")
                self.val_dataset = None
        else:
            print("⚠️ No validation data available")
            self.val_dataset = None

        # Load test dataset (may not exist)
        test_path = self.data_dir / "test"
        if test_path.exists() and any(test_path.rglob("*.png")):
            try:
                self.test_dataset = FilteredImageFolder(
                    root=test_path, transform=self.val_transform
                )
            except:
                print("⚠️ No test data available")
                self.test_dataset = None
        else:
            print("⚠️ No test data available")
            self.test_dataset = None

        print(f"Train dataset: {len(self.train_dataset)} images")
        if self.val_dataset:
            print(f"Val dataset: {len(self.val_dataset)} images")
        if self.test_dataset:
            print(f"Test dataset: {len(self.test_dataset)} images")

        # Calculate class weights for imbalanced dataset
        self.calculate_class_weights()

    def calculate_class_weights(self):
        """Calculate class weights for imbalanced dataset."""
        # Use the actual classes found in the dataset
        actual_classes = self.train_dataset.classes
        train_targets = [label for _, label in self.train_dataset.samples]

        # Count samples per class
        class_counts = np.bincount(train_targets, minlength=len(actual_classes))
        print(f"Class distribution: {dict(zip(actual_classes, class_counts, strict=False))}")

        # Calculate weights (inverse frequency)
        total_samples = len(train_targets)
        class_weights = total_samples / (len(actual_classes) * class_counts)

        # Convert to tensor
        self.class_weights = torch.FloatTensor(class_weights).to(self.device)
        self.class_names = actual_classes  # Update class names to match filtered dataset
        print(f"Class weights: {self.class_weights}")

    def setup_model(self):
        """Setup the model with transfer learning."""
        # Get actual number of classes from dataset
        num_classes = len(self.train_dataset.classes)

        if self.model_name == "efficientnet_b0":
            self.model = models.efficientnet_b0(
                weights=models.EfficientNet_B0_Weights.IMAGENET1K_V1
            )
            num_features = self.model.classifier[1].in_features
            self.model.classifier[1] = nn.Linear(num_features, num_classes)
        elif self.model_name == "resnet50":
            self.model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V1)
            num_features = self.model.fc.in_features
            self.model.fc = nn.Linear(num_features, num_classes)
        else:
            raise ValueError(f"Unsupported model: {self.model_name}")

        self.model = self.model.to(self.device)

        # Freeze early layers for transfer learning
        for param in list(self.model.parameters())[:-10]:  # Unfreeze last 10 layers
            param.requires_grad = False

        print(f"Model: {self.model_name} with {num_classes} classes")
        print(
            f"Trainable parameters: {sum(p.numel() for p in self.model.parameters() if p.requires_grad)}"
        )

    def setup_training(self):
        """Setup optimizer, loss function, and data loaders."""
        # Loss function with class weights
        self.criterion = nn.CrossEntropyLoss(weight=self.class_weights)

        # Optimizer (only train unfrozen parameters)
        self.optimizer = optim.AdamW(
            filter(lambda p: p.requires_grad, self.model.parameters()), lr=1e-3, weight_decay=1e-4
        )

        # Learning rate scheduler
        self.scheduler = optim.lr_scheduler.StepLR(self.optimizer, step_size=7, gamma=0.1)

        # Data loaders
        self.train_loader = DataLoader(
            self.train_dataset, batch_size=16, shuffle=True, num_workers=2, pin_memory=True
        )

        if self.val_dataset:
            self.val_loader = DataLoader(
                self.val_dataset, batch_size=16, shuffle=False, num_workers=2, pin_memory=True
            )
        else:
            self.val_loader = None

        if self.test_dataset:
            self.test_loader = DataLoader(
                self.test_dataset, batch_size=16, shuffle=False, num_workers=2, pin_memory=True
            )
        else:
            self.test_loader = None

    def train_epoch(self):
        """Train for one epoch."""
        self.model.train()
        running_loss = 0.0
        correct = 0
        total = 0

        for inputs, labels in tqdm(self.train_loader, desc="Training"):
            inputs, labels = inputs.to(self.device), labels.to(self.device)

            self.optimizer.zero_grad()

            outputs = self.model(inputs)
            loss = self.criterion(outputs, labels)

            loss.backward()
            self.optimizer.step()

            running_loss += loss.item()
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()

        epoch_loss = running_loss / len(self.train_loader)
        epoch_acc = 100.0 * correct / total

        return epoch_loss, epoch_acc

    def validate(self):
        """Validate the model."""
        self.model.eval()
        running_loss = 0.0
        correct = 0
        total = 0

        with torch.no_grad():
            for inputs, labels in tqdm(self.val_loader, desc="Validating"):
                inputs, labels = inputs.to(self.device), labels.to(self.device)

                outputs = self.model(inputs)
                loss = self.criterion(outputs, labels)

                running_loss += loss.item()
                _, predicted = outputs.max(1)
                total += labels.size(0)
                correct += predicted.eq(labels).sum().item()

        epoch_loss = running_loss / len(self.val_loader)
        epoch_acc = 100.0 * correct / total

        return epoch_loss, epoch_acc

    def train(self, num_epochs: int = 20, save_dir: str = "models/classifier"):
        """Train the model."""
        save_dir = Path(save_dir)
        save_dir.mkdir(exist_ok=True)

        best_acc = 0.0
        train_losses = []
        val_losses = []
        train_accs = []
        val_accs = []

        print("Starting training...")

        for epoch in range(num_epochs):
            print(f"\nEpoch {epoch+1}/{num_epochs}")

            # Train
            train_loss, train_acc = self.train_epoch()
            train_losses.append(train_loss)
            train_accs.append(train_acc)

            # Validate (if validation data available)
            if self.val_loader:
                val_loss, val_acc = self.validate()
                val_losses.append(val_loss)
                val_accs.append(val_acc)
            else:
                val_loss, val_acc = float("inf"), 0.0
                val_losses.append(val_loss)
                val_accs.append(val_acc)

            # Update learning rate
            self.scheduler.step()

            print(".4f" ".4f" ".4f" ".4f")

            # Save best model
            if val_acc > best_acc:
                best_acc = val_acc
                torch.save(
                    {
                        "epoch": epoch,
                        "model_state_dict": self.model.state_dict(),
                        "optimizer_state_dict": self.optimizer.state_dict(),
                        "val_acc": val_acc,
                        "class_names": self.class_names,
                        "model_name": self.model_name,
                    },
                    save_dir / "best_model.pth",
                )
                print(f"✓ Saved best model with validation accuracy: {val_acc:.2f}%")

        # Save final model
        torch.save(
            {
                "epoch": num_epochs,
                "model_state_dict": self.model.state_dict(),
                "optimizer_state_dict": self.optimizer.state_dict(),
                "class_names": self.class_names,
                "model_name": self.model_name,
            },
            save_dir / "final_model.pth",
        )

        # Plot training curves
        self.plot_training_curves(train_losses, val_losses, train_accs, val_accs, save_dir)

        print("\nTraining completed!")
        print(f"Best validation accuracy: {best_acc:.2f}%")
        return save_dir / "best_model.pth"

    def plot_training_curves(self, train_losses, val_losses, train_accs, val_accs, save_dir):
        """Plot training curves."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

        # Loss plot
        ax1.plot(train_losses, label="Train Loss")
        ax1.plot(val_losses, label="Val Loss")
        ax1.set_title("Training Loss")
        ax1.set_xlabel("Epoch")
        ax1.set_ylabel("Loss")
        ax1.legend()
        ax1.grid(True)

        # Accuracy plot
        ax2.plot(train_accs, label="Train Acc")
        ax2.plot(val_accs, label="Val Acc")
        ax2.set_title("Training Accuracy")
        ax2.set_xlabel("Epoch")
        ax2.set_ylabel("Accuracy (%)")
        ax2.legend()
        ax2.grid(True)

        plt.tight_layout()
        plt.savefig(save_dir / "training_curves.png", dpi=300, bbox_inches="tight")
        plt.close()

    def evaluate(self, model_path: str = None):
        """Evaluate the model on test set."""
        if model_path:
            checkpoint = torch.load(model_path, map_location=self.device)
            self.model.load_state_dict(checkpoint["model_state_dict"])

        self.model.eval()

        all_preds = []
        all_labels = []

        with torch.no_grad():
            for inputs, labels in tqdm(self.test_loader, desc="Testing"):
                inputs, labels = inputs.to(self.device), labels.to(self.device)

                outputs = self.model(inputs)
                _, predicted = outputs.max(1)

                all_preds.extend(predicted.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())

        # Calculate metrics
        print("\n" + "=" * 50)
        print("TEST RESULTS")
        print("=" * 50)

        # Classification report
        print("\nClassification Report:")
        print(
            classification_report(
                all_labels, all_preds, target_names=self.class_names, zero_division=0
            )
        )

        # Confusion matrix
        cm = confusion_matrix(all_labels, all_preds)
        print("\nConfusion Matrix:")
        print("Predicted →")
        print("Actual ↓")
        for i, class_name in enumerate(self.class_names):
            row = "  ".join("2d")
            print("12s")

        # Overall accuracy
        accuracy = np.mean(np.array(all_preds) == np.array(all_labels)) * 100
        print(".2f")

        return accuracy


def main():
    parser = argparse.ArgumentParser(description="Train egret classifier")
    parser.add_argument(
        "--data-dir", type=str, required=True, help="Path to classifier training data directory"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="efficientnet_b0",
        choices=["efficientnet_b0", "resnet50"],
        help="Model architecture to use",
    )
    parser.add_argument("--epochs", type=int, default=20, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size for training")
    parser.add_argument(
        "--save-dir", type=str, default="models/classifier", help="Directory to save trained models"
    )

    args = parser.parse_args()

    # Check if data directory exists
    if not Path(args.data_dir).exists():
        print(f"❌ Data directory not found: {args.data_dir}")
        sys.exit(1)

    # Initialize trainer
    trainer = EgretClassifierTrainer(args.data_dir, args.model)

    # Train the model
    best_model_path = trainer.train(args.epochs, args.save_dir)

    # Evaluate on test set
    print(f"\n🔍 Evaluating best model: {best_model_path}")
    trainer.evaluate(str(best_model_path))

    print("\n✅ Training completed successfully!")
    print(f"Best model saved at: {best_model_path}")
    print("Next: Integrate this model into the pipeline by updating the mock classifier.")


if __name__ == "__main__":
    main()
