#!/usr/bin/env python
"""
Test script for AI Census Helper
Run this after installing Ollama and pulling a model

Setup:
1. Install Ollama: https://ollama.com/download
2. Pull a model: ollama pull llama3.2
3. Run this script: python scripts/test_ai_census_helper.py
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'avicast_project.settings.development')
django.setup()

from apps.locations.utils.ai_census_helper import get_ai_helper
from apps.fauna.models import Species


def test_ai_availability():
    """Test if AI is available"""
    print("=" * 60)
    print("TEST 1: AI Availability Check")
    print("=" * 60)
    
    ai = get_ai_helper()
    
    if ai.is_available():
        print("[SUCCESS] AI Assistant is available!")
        print(f"   Model: {ai.ollama.model}")
        print(f"   Endpoint: {ai.ollama.base_url}")
    else:
        print("[FAILED] AI Assistant is NOT available")
        print("\nTo fix:")
        print("1. Install Ollama: https://ollama.com/download")
        print("2. Run: ollama pull llama3.2")
        print("3. Verify: ollama list")
        return False
    
    print()
    return True


def test_species_matching():
    """Test species name matching"""
    print("=" * 60)
    print("TEST 2: Species Name Matching")
    print("=" * 60)
    
    ai = get_ai_helper()
    
    # Get some known species
    known_species = list(Species.objects.values('name', 'scientific_name')[:20])
    
    if not known_species:
        print("[WARNING] No species in database. Skipping test.")
        print()
        return
    
    print(f"Testing with {len(known_species)} known species...")
    print()
    
    # Test cases
    test_cases = [
        "chinese egret",  # Lowercase
        "Black faced spoonbill",  # Variation
        "egret",  # Partial name
        "Random Bird That Doesn't Exist"  # Should not match
    ]
    
    for test_name in test_cases:
        print(f"Input: '{test_name}'")
        result = ai.match_species_name(test_name, known_species)
        
        if result['matched'] and result.get('species'):
            print(f"  [MATCH] {result['species']['name']}")
            print(f"     Confidence: {result['confidence']}")
            if 'reason' in result:
                print(f"     Reason: {result['reason']}")
        else:
            print(f"  [NO MATCH]")
            if 'reason' in result:
                print(f"     Reason: {result['reason']}")
        print()


def test_data_validation():
    """Test census data validation"""
    print("=" * 60)
    print("TEST 3: Census Data Validation")
    print("=" * 60)
    
    ai = get_ai_helper()
    
    # Test case 1: Normal data
    print("Test Case 1: Normal census observation")
    test_data = {
        'site_name': 'Main Site',
        'census_date': '2024-01-15',
        'species_name': 'Chinese Egret',
        'count': 45,
        'weather': 'Sunny'
    }
    
    result = ai.validate_census_data(test_data)
    print(f"Valid: {result['valid']}")
    if result.get('warnings'):
        print(f"Warnings: {result['warnings']}")
    if result.get('suggestions'):
        print(f"Suggestions: {result['suggestions']}")
    print()
    
    # Test case 2: Suspicious data
    print("Test Case 2: Suspicious high count")
    test_data = {
        'site_name': 'Small Pond',
        'census_date': '2024-01-15',
        'species_name': 'Chinese Egret',
        'count': 10000,  # Suspiciously high
        'weather': ''
    }
    
    result = ai.validate_census_data(test_data)
    print(f"Valid: {result['valid']}")
    if result.get('warnings'):
        print(f"Warnings: {result['warnings']}")
    if result.get('suggestions'):
        print(f"Suggestions: {result['suggestions']}")
    print()


def test_import_summary():
    """Test import results summarization"""
    print("=" * 60)
    print("TEST 4: Import Results Summary")
    print("=" * 60)
    
    ai = get_ai_helper()
    
    # Simulate import results
    results = {
        'total_rows': 150,
        'successful': 145,
        'skipped': 5,
        'created_census': 12,
        'created_observations': 145,
        'errors': [
            'Row 15: Species not found',
            'Row 42: Invalid date',
            'Row 89: Site not found',
            'Row 103: Count must be positive',
            'Row 127: Missing required field'
        ]
    }
    
    print("Generating summary for import results...")
    summary = ai.summarize_import_results(results)
    print()
    print("AI-Generated Summary:")
    print("-" * 60)
    print(summary)
    print()


def test_simple_prompt():
    """Test basic AI response"""
    print("=" * 60)
    print("TEST 5: Simple AI Prompt")
    print("=" * 60)
    
    ai = get_ai_helper()
    
    prompt = "What are the top 3 things to check when validating bird census data?"
    print(f"Question: {prompt}")
    print()
    
    response = ai.ollama.generate(
        prompt=prompt,
        system_prompt="You are a wildlife census expert. Be concise."
    )
    
    print("AI Response:")
    print("-" * 60)
    print(response)
    print()


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("AVICAST AI Census Helper - Test Suite")
    print("=" * 60)
    print()
    
    # Test 1: Availability
    if not test_ai_availability():
        print("\n[FAILED] AI is not available. Install Ollama first!")
        print("Visit: https://ollama.com/download")
        return
    
    # Test 2: Species matching
    test_species_matching()
    
    # Test 3: Data validation
    test_data_validation()
    
    # Test 4: Import summary
    test_import_summary()
    
    # Test 5: Simple prompt
    test_simple_prompt()
    
    print("=" * 60)
    print("[SUCCESS] All tests completed!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Review test results above")
    print("2. Try different models: ollama pull mistral")
    print("3. Integrate AI into import views")
    print("4. Add AI suggestions to error messages")
    print()


if __name__ == '__main__':
    main()


