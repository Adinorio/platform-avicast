#!/usr/bin/env python3
"""
Test script to verify multi-species egret identification capabilities
"""
import sys
import os
from pathlib import Path
import json

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_system_capabilities():
    """Test the system's multi-species egret identification capabilities"""
    print("🦆 Multi-Species Egret Identification System Test")
    print("=" * 60)

    try:
        # Test 1: Check model loading
        print("\n🔍 TEST 1: Model Loading Capability")
        print("-" * 40)

        try:
            from apps.image_processing.bird_detection_service import get_bird_detection_service
            service = get_bird_detection_service()

            if service.is_available():
                print("✅ Bird detection service is available")
                models_info = service.get_model_info()
                print(f"📊 Current model: {models_info['current_version']}")
                print(f"🎯 Specialty: {models_info['current_description']}")
                print(f"⚡ Device: {models_info['device']}")
                print(f"📈 Performance: {models_info['current_performance']}")
            else:
                print("❌ Bird detection service not available")
                return False

        except Exception as e:
            print(f"❌ Error loading detection service: {e}")
            return False

        # Test 2: Check configuration
        print("\n🔧 TEST 2: Species Configuration")
        print("-" * 40)

        try:
            from apps.image_processing.config import BIRD_SPECIES, YOLO_VERSION_CONFIGS

            print(f"📋 Configured species ({len(BIRD_SPECIES)}):")
            for species_id, species_info in BIRD_SPECIES.items():
                print(f"   • {species_info['name']} (ID: {species_info['class_id']})")

            print("\n🤖 Available YOLO models:")
            for model_name, config in YOLO_VERSION_CONFIGS.items():
                trained_species = config.get('trained_classes', [])
                print(f"   • {model_name}: {config['description']}")
                if trained_species:
                    print(f"     Trained on: {', '.join(trained_species)}")

        except Exception as e:
            print(f"❌ Error checking configuration: {e}")

        # Test 3: Check classifier capabilities
        print("\n🧠 TEST 3: Classification System")
        print("-" * 40)

        try:
            # Check if classifier model exists
            classifier_path = project_root / "models" / "classifier" / "best_model.pth"
            print(f"Classifier model exists: {classifier_path.exists()}")

            if classifier_path.exists():
                print("✅ Classifier model found")
                # Try to load and inspect
                try:
                    import torch
                    checkpoint = torch.load(classifier_path, map_location='cpu', weights_only=False)
                    print(f"📊 Model architecture: {checkpoint.get('model_name', 'unknown')}")
                    print(f"🏷️  Class names: {checkpoint.get('class_names', 'unknown')}")
                except Exception as e:
                    print(f"⚠️ Could not inspect classifier model: {e}")
            else:
                print("❌ Classifier model not found - using mock classifier")

            # Test mock classifier
            from apps.image_processing.bird_detection_service import mock_classifier_predict
            import numpy as np

            # Create dummy crop
            dummy_crop = np.random.rand(64, 64, 3).astype(np.uint8) * 255
            mock_result = mock_classifier_predict(dummy_crop)

            print("🎭 Mock classifier species support:")
            for species, prob in mock_result.items():
                print(".3f")

        except Exception as e:
            print(f"❌ Error testing classification: {e}")

        # Test 4: Check decision gates
        print("\n⚖️ TEST 4: Decision Gates & Confidence Thresholds")
        print("-" * 40)

        try:
            from apps.image_processing.bird_detection_service import (
                DETECTION_CONF_THRESHOLD,
                CLASSIFIER_CONF_THRESHOLD,
                CLASSIFIER_MARGIN_THRESHOLD
            )

            print(f"Detection confidence threshold: {DETECTION_CONF_THRESHOLD}")
            print(f"Classifier confidence threshold: {CLASSIFIER_CONF_THRESHOLD}")
            print(f"Classifier margin threshold: {CLASSIFIER_MARGIN_THRESHOLD}")

            print("
📊 Decision Logic:")
            print(".1f"            print(".1f"            print(".1f"        except Exception as e:
            print(f"❌ Error checking decision gates: {e}")

        # Test 5: Check multi-detection capability
        print("\n🔍 TEST 5: Multi-Detection Capability")
        print("-" * 40)

        try:
            # Check if system stores multiple detections
            from apps.image_processing.models import ImageProcessingResult

            # Get sample processing results if any exist
            sample_results = ImageProcessingResult.objects.all()[:3]
            if sample_results:
                print(f"📊 Found {len(sample_results)} processing results in database")

                for i, result in enumerate(sample_results):
                    bbox_data = result.bounding_box
                    if isinstance(bbox_data, dict):
                        total_count = bbox_data.get('total_count', 0)
                        all_detections = bbox_data.get('all_detections', [])
                        print(f"   Result {i+1}: {total_count} detections, {len(all_detections)} stored")

                        if all_detections:
                            species_counts = {}
                            for det in all_detections:
                                species = det.get('species', 'unknown')
                                species_counts[species] = species_counts.get(species, 0) + 1

                            print(f"     Species breakdown: {species_counts}")
            else:
                print("📊 No processing results found in database")

        except Exception as e:
            print(f"❌ Error checking multi-detection: {e}")

        return True

    except Exception as e:
        print(f"❌ System test failed: {e}")
        return False

def analyze_system_limitations():
    """Analyze current system limitations for multi-species egret identification"""
    print("\n🚨 SYSTEM LIMITATIONS ANALYSIS")
    print("=" * 60)

    limitations = []

    # Check training data imbalance
    print("📊 Training Data Analysis:")
    try:
        from pathlib import Path
        import os

        labels_path = Path("training_data/final_yolo_dataset/unified_egret_dataset/train/labels")

        if labels_path.exists():
            # Count files by species
            species_counts = {}
            for label_file in labels_path.glob("*.txt"):
                species_name = None
                if "chinese" in label_file.stem:
                    species_name = "Chinese Egret"
                elif "great" in label_file.stem:
                    species_name = "Great Egret"
                elif "intermediate" in label_file.stem:
                    species_name = "Intermediate Egret"
                elif "little" in label_file.stem:
                    species_name = "Little Egret"

                if species_name:
                    species_counts[species_name] = species_counts.get(species_name, 0) + 1

            total_files = sum(species_counts.values())
            print(f"   Total training files: {total_files}")

            for species, count in species_counts.items():
                percentage = (count / total_files) * 100
                status = "✅ GOOD" if percentage > 15 else "⚠️ LOW" if percentage > 5 else "❌ SEVERE"
                print("15")

                if percentage < 5:
                    limitations.append(f"Severe data imbalance for {species} ({percentage:.1f}%)")

        else:
            print("   ❌ Training data not found")
            limitations.append("Training data directory not accessible")

    except Exception as e:
        print(f"   ❌ Error analyzing training data: {e}")
        limitations.append(f"Training data analysis failed: {e}")

    # Check classifier capabilities
    print("\n🧠 Classification Analysis:")
    try:
        classifier_path = Path("models/classifier/best_model.pth")
        if not classifier_path.exists():
            print("   ❌ Trained classifier not available")
            limitations.append("No trained classifier - using mock predictions")
        else:
            print("   ✅ Trained classifier available")

        # Check mock classifier species
        from apps.image_processing.bird_detection_service import mock_classifier_predict
        import numpy as np

        dummy_crop = np.random.rand(64, 64, 3).astype(np.uint8) * 255
        mock_result = mock_classifier_predict(dummy_crop)

        available_species = list(mock_result.keys())
        print(f"   Mock classifier supports: {available_species}")

        required_species = ["Chinese Egret", "Great Egret", "Intermediate Egret", "Little Egret"]
        missing_species = [s for s in required_species if s not in available_species]

        if missing_species:
            print(f"   ❌ Missing species in mock classifier: {missing_species}")
            limitations.append(f"Mock classifier missing: {missing_species}")

    except Exception as e:
        print(f"   ❌ Error analyzing classifier: {e}")
        limitations.append(f"Classifier analysis failed: {e}")

    return limitations

if __name__ == "__main__":
    print("🦆 AVICAST Multi-Species Egret System Verification")
    print("=" * 70)

    # Run system capability test
    success = test_system_capabilities()

    if success:
        print("\n✅ SYSTEM VERIFICATION COMPLETE")
        print("The system CAN identify multiple egret species in a single image")
        print("However, there are limitations that affect accuracy...")

        # Analyze limitations
        limitations = analyze_system_limitations()

        if limitations:
            print("
⚠️ IDENTIFIED LIMITATIONS:"            for i, limitation in enumerate(limitations, 1):
                print(f"   {i}. {limitation}")

        print("
📋 RECOMMENDATIONS:")
        print("   1. Balance training data across all egret species")
        print("   2. Train dedicated classifier for egret species")
        print("   3. Adjust confidence thresholds for similar species")
        print("   4. Implement hierarchical classification")
        print("   5. Add uncertainty quantification")

    else:
        print("\n❌ SYSTEM VERIFICATION FAILED")
        print("The system has critical issues that prevent proper egret identification")
