#!/usr/bin/env python3
"""
Retrain Stage-2 classifier with expanded egret dataset (all 4 classes).

This script:
1. Loads the expanded training data (from collect_training_data.py)
2. Retrains EfficientNet on all 4 egret classes
3. Handles class imbalance with weighted loss
4. Evaluates performance and saves the updated model
"""

import os
import sys
import json
import argparse
from pathlib import Path
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, WeightedRandomSampler
from torchvision import datasets, transforms, models
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')


class EgretClassifierRetrainer:
    """Retrain egret classifier with expanded dataset."""

    def __init__(self, data_dir: str, model_name: str = 'efficientnet_b0',
                 pretrained_model_path: str = None):
        self.data_dir = Path(data_dir)
        self.model_name = model_name
        self.pretrained_path = pretrained_model_path
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        # All 4 egret classes
        self.classes = ['Chinese Egret', 'Great Egret', 'Intermediate Egret', 'Little Egret']
        self.num_classes = len(self.classes)

        # Setup transforms
        self.setup_transforms()

        # Load datasets
        self.load_datasets()

        # Setup model
        self.setup_model()

        # Setup training
        self.setup_training()

    def setup_transforms(self):
        """Setup data transforms."""
        self.train_transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomRotation(15),
            transforms.ColorJitter(brightness=0.1, contrast=0.1, saturation=0.1),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

        self.val_transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

    def load_datasets(self):
        """Load training and validation datasets."""
        print(f"Loading data from: {self.data_dir}")

        # Load training dataset
        train_dir = self.data_dir / 'train'
        if not train_dir.exists():
            raise FileNotFoundError(f"Training directory not found: {train_dir}")

        self.train_dataset = datasets.ImageFolder(
            root=train_dir,
            transform=self.train_transform
        )

        # Update classes based on what's actually in the dataset
        self.classes = self.train_dataset.classes
        self.num_classes = len(self.classes)
        print(f"Found classes: {self.classes}")

        # Load validation dataset if available
        val_dir = self.data_dir / 'val'
        if val_dir.exists():
            self.val_dataset = datasets.ImageFolder(
                root=val_dir,
                transform=self.val_transform
            )
        else:
            print("No validation directory found - will validate on training set")
            self.val_dataset = None

        print(f"Training samples: {len(self.train_dataset)}")
        if self.val_dataset:
            print(f"Validation samples: {len(self.val_dataset)}")

        # Calculate class weights
        self.calculate_class_weights()

    def calculate_class_weights(self):
        """Calculate weights for imbalanced classes."""
        train_targets = [label for _, label in self.train_dataset.samples]
        class_counts = np.bincount(train_targets, minlength=self.num_classes)

        print("Class distribution:")
        for i, cls in enumerate(self.classes):
            print(f"  {cls}: {class_counts[i]}")

        # Calculate inverse frequency weights
        total_samples = len(train_targets)
        class_weights = total_samples / (self.num_classes * class_counts)

        # Normalize weights
        class_weights = class_weights / class_weights.sum() * self.num_classes

        self.class_weights = torch.FloatTensor(class_weights).to(self.device)
        print(f"Class weights: {self.class_weights}")

    def setup_model(self):
        """Setup model with transfer learning."""
        if self.model_name == 'efficientnet_b0':
            # Load pretrained model
            self.model = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.IMAGENET1K_V1)

            # Modify classifier for our number of classes
            num_features = self.model.classifier[1].in_features
            self.model.classifier[1] = nn.Linear(num_features, self.num_classes)

        elif self.model_name == 'resnet50':
            self.model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V1)
            num_features = self.model.fc.in_features
            self.model.fc = nn.Linear(num_features, self.num_classes)

        else:
            raise ValueError(f"Unsupported model: {self.model_name}")

        self.model = self.model.to(self.device)

        # Load pretrained weights if available
        if self.pretrained_path and Path(self.pretrained_path).exists():
            print(f"Loading pretrained weights from: {self.pretrained_path}")
            checkpoint = torch.load(self.pretrained_path, map_location=self.device, weights_only=False)

            # Handle different checkpoint formats
            if 'model_state_dict' in checkpoint:
                state_dict = checkpoint['model_state_dict']
            else:
                state_dict = checkpoint

            # Load weights, ignoring classifier layer if sizes don't match
            model_dict = self.model.state_dict()
            pretrained_dict = {k: v for k, v in state_dict.items()
                             if k in model_dict and v.shape == model_dict[k].shape}

            model_dict.update(pretrained_dict)
            self.model.load_state_dict(model_dict)
            print(f"Loaded {len(pretrained_dict)}/{len(model_dict)} layers from pretrained model")

        # Freeze early layers, unfreeze later layers for fine-tuning
        for param in list(self.model.parameters())[:-10]:
            param.requires_grad = False

        trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        print(f"Model: {self.model_name} with {self.num_classes} classes")
        print(f"Trainable parameters: {trainable_params}")

    def setup_training(self):
        """Setup training components."""
        # Loss function with class weights
        self.criterion = nn.CrossEntropyLoss(weight=self.class_weights)

        # Optimizer (only train unfrozen parameters)
        self.optimizer = optim.AdamW(
            filter(lambda p: p.requires_grad, self.model.parameters()),
            lr=1e-3,
            weight_decay=1e-4
        )

        # Learning rate scheduler
        self.scheduler = optim.lr_scheduler.StepLR(self.optimizer, step_size=5, gamma=0.5)

        # Data loaders
        self.train_loader = DataLoader(
            self.train_dataset,
            batch_size=16,
            shuffle=True,
            num_workers=2,
            pin_memory=True
        )

        if self.val_dataset:
            self.val_loader = DataLoader(
                self.val_dataset,
                batch_size=16,
                shuffle=False,
                num_workers=2,
                pin_memory=True
            )

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
        epoch_acc = 100. * correct / total

        return epoch_loss, epoch_acc

    def validate(self):
        """Validate the model."""
        if not self.val_dataset:
            return 0.0, 0.0

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
        epoch_acc = 100. * correct / total

        return epoch_loss, epoch_acc

    def train(self, num_epochs: int = 15, save_dir: str = 'models/classifier'):
        """Train the model."""
        save_dir = Path(save_dir)
        save_dir.mkdir(exist_ok=True)

        best_acc = 0.0
        train_losses = []
        val_losses = []
        train_accs = []
        val_accs = []

        print("\n" + "="*50)
        print("STARTING RETRAINING WITH EXPANDED DATASET")
        print("="*50)
        print(f"Model: {self.model_name}")
        print(f"Classes: {self.classes}")
        print(f"Training samples: {len(self.train_dataset)}")
        if self.val_dataset:
            print(f"Validation samples: {len(self.val_dataset)}")
        print(f"Epochs: {num_epochs}")
        print("="*50)

        for epoch in range(num_epochs):
            print(f"\nEpoch {epoch+1}/{num_epochs}")

            # Train
            train_loss, train_acc = self.train_epoch()
            train_losses.append(train_loss)
            train_accs.append(train_acc)

            # Validate
            if self.val_dataset:
                val_loss, val_acc = self.validate()
                val_losses.append(val_loss)
                val_accs.append(val_acc)
            else:
                val_loss, val_acc = 0.0, 0.0
                val_losses.append(val_loss)
                val_accs.append(val_acc)

            # Update learning rate
            self.scheduler.step()

            # Print progress
            if self.val_dataset:
                print(".4f"
                      ".4f")
            else:
                print(".4f")

            # Save best model
            current_acc = val_acc if self.val_dataset else train_acc
            if current_acc > best_acc:
                best_acc = current_acc
                torch.save({
                    'epoch': epoch,
                    'model_state_dict': self.model.state_dict(),
                    'optimizer_state_dict': self.optimizer.state_dict(),
                    'val_acc': current_acc,
                    'classes': self.classes,
                    'model_name': self.model_name,
                    'num_classes': self.num_classes
                }, save_dir / 'best_model_retrained.pth')
                print(f"✓ Saved best model with accuracy: {current_acc:.2f}%")

        # Save final model
        torch.save({
            'epoch': num_epochs,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'classes': self.classes,
            'model_name': self.model_name,
            'num_classes': self.num_classes
        }, save_dir / 'final_model_retrained.pth')

        # Plot training curves
        self.plot_training_curves(train_losses, val_losses, train_accs, val_accs, save_dir)

        print("
Training completed!"        print(".2f"
        return save_dir / 'best_model_retrained.pth'

    def plot_training_curves(self, train_losses, val_losses, train_accs, val_accs, save_dir):
        """Plot training curves."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

        # Loss plot
        ax1.plot(train_losses, label='Train Loss')
        if self.val_dataset:
            ax1.plot(val_losses, label='Val Loss')
        ax1.set_title('Training Loss')
        ax1.set_xlabel('Epoch')
        ax1.set_ylabel('Loss')
        ax1.legend()
        ax1.grid(True)

        # Accuracy plot
        ax2.plot(train_accs, label='Train Acc')
        if self.val_dataset:
            ax2.plot(val_accs, label='Val Acc')
        ax2.set_title('Training Accuracy')
        ax2.set_xlabel('Epoch')
        ax2.set_ylabel('Accuracy (%)')
        ax2.legend()
        ax2.grid(True)

        plt.tight_layout()
        plt.savefig(save_dir / 'retraining_curves.png', dpi=300, bbox_inches='tight')
        plt.close()

    def evaluate(self, model_path: str = None, test_dir: str = None):
        """Evaluate the model on test set."""
        if model_path:
            checkpoint = torch.load(model_path, map_location=self.device, weights_only=False)
            self.model.load_state_dict(checkpoint['model_state_dict'])

        # Use test directory if provided, otherwise use validation
        if test_dir and Path(test_dir).exists():
            test_dataset = datasets.ImageFolder(
                root=test_dir,
                transform=self.val_transform
            )
            test_loader = DataLoader(test_dataset, batch_size=16, shuffle=False)
        elif self.val_dataset:
            test_loader = self.val_loader
        else:
            print("No test/validation data available for evaluation")
            return 0.0

        self.model.eval()
        all_preds = []
        all_labels = []

        with torch.no_grad():
            for inputs, labels in tqdm(test_loader, desc="Testing"):
                inputs, labels = inputs.to(self.device), labels.to(self.device)

                outputs = self.model(inputs)
                _, predicted = outputs.max(1)

                all_preds.extend(predicted.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())

        # Calculate metrics
        print("\n" + "="*60)
        print("MODEL EVALUATION RESULTS")
        print("="*60)

        # Classification report
        print("\nClassification Report:")
        print(classification_report(all_labels, all_preds,
                                  target_names=self.classes,
                                  zero_division=0))

        # Confusion matrix
        cm = confusion_matrix(all_labels, all_preds)
        print("\nConfusion Matrix:")
        print("Predicted →")
        print("Actual ↓")
        for i, class_name in enumerate(self.classes):
            row = "  ".join("2d")
            print("20s")

        # Overall accuracy
        accuracy = np.mean(np.array(all_preds) == np.array(all_labels)) * 100
        print(".2f")

        return accuracy


def main():
    parser = argparse.ArgumentParser(description='Retrain egret classifier with expanded data')
    parser.add_argument('--data-dir', type=str, required=True,
                       help='Path to expanded training data directory')
    parser.add_argument('--model', type=str, default='efficientnet_b0',
                       choices=['efficientnet_b0', 'resnet50'],
                       help='Model architecture to use')
    parser.add_argument('--pretrained', type=str, default='models/classifier/best_model.pth',
                       help='Path to pretrained model weights')
    parser.add_argument('--epochs', type=int, default=15,
                       help='Number of training epochs')
    parser.add_argument('--save-dir', type=str, default='models/classifier',
                       help='Directory to save trained models')

    args = parser.parse_args()

    # Check if data directory exists
    if not Path(args.data_dir).exists():
        print(f"❌ Data directory not found: {args.data_dir}")
        print("Run collect_training_data.py first to create the expanded dataset.")
        sys.exit(1)

    # Initialize retrainer
    retrainer = EgretClassifierRetrainer(
        args.data_dir,
        args.model,
        args.pretrained if Path(args.pretrained).exists() else None
    )

    # Train the model
    best_model_path = retrainer.train(args.epochs, args.save_dir)

    # Evaluate on test set
    print(f"\n🔍 Evaluating best retrained model: {best_model_path}")
    test_dir = Path(args.data_dir) / 'test'
    if test_dir.exists():
        retrainer.evaluate(str(best_model_path), str(test_dir))
    else:
        retrainer.evaluate(str(best_model_path))

    print("
✅ Retraining completed successfully!"    print(f"Best model saved at: {best_model_path}")
    print("\nNext steps:")
    print("1. Update bird_detection_service.py to use the new model")
    print("2. Test the updated pipeline with real egret images")
    print("3. Monitor performance and iterate as needed")


if __name__ == '__main__':
    main()



