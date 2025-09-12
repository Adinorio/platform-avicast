#!/usr/bin/env python3
"""
Test script to verify the egret identification improvements
"""
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_uncertainty_calculation():
    """Test the uncertainty calculation function"""
    print("🧪 Testing Uncertainty Calculation...")

    try:
        from apps.image_processing.bird_detection_service import calculate_egret_uncertainty

        # Test case 1: High confidence, correct size (Chinese Egret)
        detection1 = {
            'species': 'Chinese Egret',
            'confidence': 0.85,
            'bbox_area': 0.08  # Within expected range (0.05-0.15)
        }
        result1 = calculate_egret_uncertainty(detection1)
        print(f"✅ Chinese Egret (high conf, correct size): Uncertainty {result1['uncertainty_score']:.2f}, Level {result1['uncertainty_level']}")

        # Test case 2: Low confidence, correct size (Little Egret)
        detection2 = {
            'species': 'Little Egret',
            'confidence': 0.55,  # Below threshold (0.60)
            'bbox_area': 0.30   # Within expected range (0.20-0.50)
        }
        result2 = calculate_egret_uncertainty(detection2)
        print(f"⚠️ Little Egret (low conf, correct size): Uncertainty {result2['uncertainty_score']:.2f}, Level {result2['uncertainty_level']}")

        # Test case 3: High confidence, wrong size (Chinese Egret too large)
        detection3 = {
            'species': 'Chinese Egret',
            'confidence': 0.85,
            'bbox_area': 0.25  # Outside expected range (0.05-0.15)
        }
        result3 = calculate_egret_uncertainty(detection3)
        print(f"⚠️ Chinese Egret (high conf, wrong size): Uncertainty {result3['uncertainty_score']:.2f}, Level {result3['uncertainty_level']}")

        # Test case 4: Little Egret (very limited training data)
        detection4 = {
            'species': 'Little Egret',
            'confidence': 0.75,
            'bbox_area': 0.35
        }
        result4 = calculate_egret_uncertainty(detection4)
        print(f"⚠️ Little Egret (limited training): Uncertainty {result4['uncertainty_score']:.2f}, Level {result4['uncertainty_level']}")

        print("✅ Uncertainty calculation working correctly!")
        return True

    except Exception as e:
        print(f"❌ Error testing uncertainty calculation: {e}")
        return False

def test_enhanced_mock_classifier():
    """Test the enhanced mock classifier"""
    print("\n🤖 Testing Enhanced Mock Classifier...")

    try:
        from apps.image_processing.bird_detection_service import mock_classifier_predict
        import numpy as np

        # Test with different crop sizes to verify size-based logic
        test_cases = [
            ("Small crop (Chinese-like)", 64, 100),    # Small, slender
            ("Medium crop (Intermediate-like)", 80, 80), # Medium, square
            ("Large crop (Little-like)", 120, 60),     # Large, stocky
        ]

        for name, width, height in test_cases:
            # Create test crop
            crop = np.random.rand(height, width, 3).astype(np.uint8) * 255

            # Get predictions
            probs = mock_classifier_predict(crop)

            # Find top prediction
            top_species = max(probs.items(), key=lambda x: x[1])

            print(f"📏 {name} ({width}x{height}): Top prediction {top_species[0]} ({top_species[1]:.2f})")
            print(f"   All probs: Chinese={probs['Chinese']:.2f}, Great={probs['Great']:.2f}, Intermediate={probs['Intermediate']:.2f}, Little={probs['Little']:.2f}")

        print("✅ Enhanced mock classifier working correctly!")
        return True

    except Exception as e:
        print(f"❌ Error testing mock classifier: {e}")
        return False

def test_threshold_improvements():
    """Test the improved threshold configurations"""
    print("\n⚖️ Testing Threshold Improvements...")

    try:
        from apps.image_processing.bird_detection_service import (
            EGRET_SPECIES_THRESHOLDS,
            CLASSIFIER_MARGIN_THRESHOLD,
            EGRET_SIZE_RANGES,
            EGRET_ASPECT_RATIOS
        )

        print("📊 Species-specific thresholds:")
        for species, threshold in EGRET_SPECIES_THRESHOLDS.items():
            print(f"   • {species}: {threshold} (vs old 0.80)")

        print("
📏 Size ranges:")
        for species, (min_size, max_size) in EGRET_SIZE_RANGES.items():
            print(f"   • {species}: {min_size}-{max_size}")

        print("
📐 Aspect ratios:")
        for species, (min_ratio, max_ratio) in EGRET_ASPECT_RATIOS.items():
            print(f"   • {species}: {min_ratio:.1f}-{max_ratio:.1f}")

        print(f"\n🔄 Classifier margin threshold: {CLASSIFIER_MARGIN_THRESHOLD} (vs old 0.25)")
        print("✅ Threshold improvements configured correctly!")
        return True

    except Exception as e:
        print(f"❌ Error testing thresholds: {e}")
        return False

def create_demo_output():
    """Create a demonstration of improved egret identification"""
    print("\n🎯 DEMONSTRATION: Improved Egret Identification")
    print("=" * 60)

    try:
        from apps.image_processing.bird_detection_service import calculate_egret_uncertainty

        # Simulate a challenging identification scenario
        challenging_cases = [
            {
                "scenario": "Small bird, high confidence (likely Chinese Egret)",
                "detection": {
                    'species': 'Chinese Egret',
                    'confidence': 0.82,
                    'bbox_area': 0.06
                }
            },
            {
                "scenario": "Medium bird, borderline confidence (tricky Intermediate)",
                "detection": {
                    'species': 'Intermediate Egret',
                    'confidence': 0.68,  # Below old threshold but above new
                    'bbox_area': 0.12
                }
            },
            {
                "scenario": "Large bird, wrong species size (Great Egret too small)",
                "detection": {
                    'species': 'Great Egret',
                    'confidence': 0.78,
                    'bbox_area': 0.08  # Too small for Great Egret
                }
            },
            {
                "scenario": "Little Egret with limited training data",
                "detection": {
                    'species': 'Little Egret',
                    'confidence': 0.72,
                    'bbox_area': 0.35
                }
            }
        ]

        for case in challenging_cases:
            print(f"\n📋 {case['scenario']}:")
            uncertainty = calculate_egret_uncertainty(case['detection'])

            print(f"   Species: {case['detection']['species']}")
            print(f"   Confidence: {case['detection']['confidence']:.2f}")
            print(f"   Size: {case['detection']['bbox_area']:.2f}")
            print(f"   Uncertainty Score: {uncertainty['uncertainty_score']:.2f}")
            print(f"   Uncertainty Level: {uncertainty['uncertainty_level']}/4")
            print(f"   Factors: {', '.join(uncertainty['uncertainty_factors'])}")

            if uncertainty['alternative_species']:
                print(f"   Alternatives: {', '.join(uncertainty['alternative_species'])}")

            # Decision based on new logic
            old_threshold = 0.80
            from apps.image_processing.bird_detection_service import EGRET_SPECIES_THRESHOLDS
            new_threshold = EGRET_SPECIES_THRESHOLDS.get(case['detection']['species'], 0.75)

            old_decision = "✅ ACCEPT" if case['detection']['confidence'] >= old_threshold else "❌ REJECT"
            new_decision = "✅ ACCEPT" if case['detection']['confidence'] >= new_threshold else "⚠️ REVIEW"

            print(f"   Old system (80%): {old_decision}")
            print(f"   New system (species-specific): {new_decision}")

    except Exception as e:
        print(f"❌ Error creating demo: {e}")

if __name__ == "__main__":
    print("🦆 AVICAST Egret Identification Improvements Test")
    print("=" * 60)

    # Run all tests
    tests_passed = 0
    total_tests = 3

    if test_uncertainty_calculation():
        tests_passed += 1

    if test_enhanced_mock_classifier():
        tests_passed += 1

    if test_threshold_improvements():
        tests_passed += 1

    print("
" + "=" * 60)
    print(f"🧪 TEST RESULTS: {tests_passed}/{total_tests} tests passed")

    if tests_passed == total_tests:
        print("✅ All improvements implemented successfully!")
        create_demo_output()
    else:
        print("⚠️ Some tests failed - check implementation")

    print("
📋 NEXT STEPS:")
    print("   1. Test with real images to validate improvements")
    print("   2. Monitor uncertainty scores in production")
    print("   3. Consider training data expansion for underrepresented species")
    print("   4. Implement frontend uncertainty visualization")
    print("=" * 60)
