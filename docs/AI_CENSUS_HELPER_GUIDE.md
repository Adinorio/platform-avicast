

# AI Census Helper - Local LLM Integration

## Overview

AVICAST now supports **offline AI assistance** for census data management using **Ollama** - a local LLM runtime that runs entirely on your machine.

**Key Features:**
- ✅ **100% Offline** - No internet required after setup
- ✅ **Privacy First** - All data stays on your local machine
- ✅ **Species Matching** - AI helps match user input to known species
- ✅ **Data Validation** - AI checks for suspicious or incorrect data
- ✅ **Smart Suggestions** - AI provides helpful error corrections
- ✅ **Natural Summaries** - AI generates friendly import summaries

**AGENTS.md Compliance:** §6.1 Security - Local-first deployment, no external API calls

---

## Installation

### Step 1: Install Ollama

**Windows:**
1. Download from: https://ollama.com/download
2. Run `OllamaSetup.exe`
3. Restart your terminal

**Mac:**
```bash
brew install ollama
```

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Step 2: Download a Model

**Recommended Models:**

```bash
# Llama 3.2 (3B) - Fast, good balance
ollama pull llama3.2

# Mistral (7B) - More accurate, slower
ollama pull mistral

# Phi-3 (3.8B) - Microsoft's efficient model
ollama pull phi3
```

**Model Comparison:**

| Model | Size | Speed | Accuracy | Best For |
|-------|------|-------|----------|----------|
| llama3.2 | 3GB | Fast | Good | General use, quick responses |
| mistral | 7GB | Medium | Better | Complex matching, validation |
| phi3 | 4GB | Fast | Good | Balanced performance |

### Step 3: Verify Installation

```bash
# List installed models
ollama list

# Test the model
ollama run llama3.2
>>> Hello! (press Ctrl+D to exit)
```

### Step 4: Install Python Dependencies

```bash
pip install requests
```

---

## Quick Test

Run the test suite to verify everything works:

```bash
python scripts/test_ai_census_helper.py
```

**Expected Output:**
```
============================================================
AVICAST AI Census Helper - Test Suite
============================================================

TEST 1: AI Availability Check
✅ AI Assistant is available!
   Model: llama3.2
   Endpoint: http://localhost:11434

TEST 2: Species Name Matching
Testing with 20 known species...

Input: 'chinese egret'
  ✅ Matched: Chinese Egret
     Confidence: 0.95
     Reason: Exact match (case-insensitive)

...
```

---

## Usage Examples

### 1. Species Name Matching

```python
from apps.locations.utils.ai_census_helper import get_ai_helper
from apps.fauna.models import Species

# Get AI helper
ai = get_ai_helper()

# Get known species
known_species = Species.objects.values('name', 'scientific_name')

# User enters: "chinese egret" (lowercase, informal)
user_input = "chinese egret"

# AI matches to correct species
result = ai.match_species_name(user_input, known_species)

if result['matched']:
    print(f"Matched to: {result['species']['name']}")
    print(f"Scientific: {result['species']['scientific_name']}")
    print(f"Confidence: {result['confidence']}")
else:
    print(f"No match found: {result['reason']}")
```

### 2. Data Validation

```python
# Census data from import
data = {
    'site_name': 'Main Site',
    'census_date': '2024-01-15',
    'species_name': 'Chinese Egret',
    'count': 10000,  # Suspiciously high!
    'weather': 'Sunny'
}

# AI validates the data
result = ai.validate_census_data(data)

if not result['valid']:
    print("⚠️ Validation issues found:")
    for warning in result['warnings']:
        print(f"  - {warning}")
    
    print("\n💡 Suggestions:")
    for suggestion in result['suggestions']:
        print(f"  - {suggestion}")
```

### 3. Import Summary

```python
# After import completes
results = {
    'total_rows': 150,
    'successful': 145,
    'skipped': 5,
    'created_census': 12,
    'created_observations': 145,
    'errors': [...]
}

# AI generates friendly summary
summary = ai.summarize_import_results(results)
print(summary)

# Output: "Great work! You successfully imported 145 out of 150 
# bird observations, creating 12 new census records. There were 
# 5 rows with minor issues that were skipped - mostly related 
# to species name matching."
```

---

## Integration with Import/Export

The AI helper can be integrated into your existing import flow:

### Enhanced Import with AI

```python
# In apps/locations/utils/excel_handler.py
from .ai_census_helper import get_ai_helper

class CensusExcelHandler:
    
    @staticmethod
    def import_from_excel(file, user, use_ai=True):
        ai = get_ai_helper() if use_ai else None
        
        # ... existing code ...
        
        # When species not found, try AI matching
        if not species and ai and ai.is_available():
            known_species = Species.objects.values('name', 'scientific_name')
            match_result = ai.match_species_name(species_name, known_species)
            
            if match_result['matched'] and match_result['confidence'] > 0.8:
                species = Species.objects.get(name=match_result['species']['name'])
                results['ai_matches'] += 1
        
        # ... continue import ...
```

---

## Performance Considerations

### Response Times (Approximate)

| Task | llama3.2 | mistral | phi3 |
|------|----------|---------|------|
| Species matching | 1-2s | 2-3s | 1-2s |
| Data validation | 2-3s | 3-5s | 2-3s |
| Summary generation | 2-4s | 4-6s | 2-4s |

### Resource Usage

| Model | RAM | CPU | GPU (Optional) |
|-------|-----|-----|----------------|
| llama3.2 | 4GB | Moderate | Accelerates 5x |
| mistral | 8GB | High | Accelerates 5x |
| phi3 | 5GB | Moderate | Accelerates 5x |

**Tip:** Use GPU acceleration if available (Ollama auto-detects CUDA/Metal)

---

## Configuration

### Change Model

```python
# Use a different model
ai = get_ai_helper(model="mistral")
```

### Custom Prompts

```python
# Custom system prompt for specific behavior
prompt = "What species is this?"
system_prompt = "You are a bird identification expert specializing in Asian waterfowl."

response = ai.ollama.generate(prompt, system_prompt)
```

### Timeout Settings

```python
# Adjust timeout for slower models
ai.ollama.timeout = 60  # seconds
```

---

## Troubleshooting

### Issue: "AI unavailable"

**Solutions:**
1. Check Ollama is running: `ollama list`
2. Pull the model: `ollama pull llama3.2`
3. Verify endpoint: http://localhost:11434
4. Check firewall settings

### Issue: Slow responses

**Solutions:**
1. Use smaller model: `ollama pull llama3.2` instead of `mistral`
2. Enable GPU acceleration (auto-detected)
3. Reduce prompt length (limit known species to 50)
4. Close other applications

### Issue: Incorrect matches

**Solutions:**
1. Use larger model for better accuracy
2. Increase confidence threshold (e.g., > 0.9)
3. Add more context to prompts
4. Fine-tune system prompts

### Issue: High memory usage

**Solutions:**
1. Use smaller model (phi3 or llama3.2)
2. Stop Ollama when not in use: `ollama stop`
3. Limit concurrent requests
4. Clear Ollama cache periodically

---

## Advanced Usage

### Batch Processing

```python
# Process multiple species names efficiently
ai = get_ai_helper()
known_species = list(Species.objects.values('name', 'scientific_name'))

for row in excel_rows:
    result = ai.match_species_name(row['species'], known_species)
    # Cache results to avoid re-matching
```

### Custom AI Features

```python
# Add your own AI functions
class CustomAIHelper(AICensusHelper):
    
    def suggest_census_schedule(self, site_id):
        """AI suggests optimal census schedule"""
        prompt = f"Based on bird migration patterns, suggest optimal..."
        return self.ollama.generate(prompt)
    
    def analyze_trends(self, site_data):
        """AI analyzes population trends"""
        prompt = f"Analyze these bird population trends..."
        return self.ollama.generate(prompt)
```

---

## Best Practices

### 1. Offline-First
- ✅ Always check `ai.is_available()` before using
- ✅ Provide fallback behavior when AI unavailable
- ✅ Don't make AI required for core functionality

### 2. User Feedback
- ✅ Show AI confidence scores
- ✅ Allow users to override AI suggestions
- ✅ Log AI decisions for review

### 3. Performance
- ✅ Use smaller models for real-time features
- ✅ Cache common queries
- ✅ Run AI tasks in background when possible

### 4. Privacy
- ✅ All data stays local (Ollama is offline)
- ✅ No data sent to external APIs
- ✅ Complies with AGENTS.md security requirements

---

## Future Enhancements

**Planned Features:**
- [ ] Fine-tune models on your specific bird species
- [ ] Auto-correct common data entry errors
- [ ] Predict likely species for a site/season
- [ ] Generate census reports with AI summaries
- [ ] OCR for handwritten field notes
- [ ] Voice-to-text for field observations

---

## FAQ

**Q: Does this require internet?**  
A: No! After initial model download, everything runs offline.

**Q: Can I use ChatGPT/Claude instead?**  
A: Not recommended. Those require internet and violate AVICAST's local-first principle.

**Q: Which model should I use?**  
A: Start with `llama3.2` - it's fast and accurate for most tasks.

**Q: Can I run this on a slow computer?**  
A: Yes! Use `llama3.2` or `phi3` for better performance on modest hardware.

**Q: Is my census data safe?**  
A: Yes! All AI processing happens locally. No data leaves your machine.

---

## Summary

**Setup Time:** 5-10 minutes  
**Works Offline:** ✅ Yes  
**Privacy:** ✅ 100% Local  
**Cost:** ✅ Free  
**Performance:** ✅ Good (1-5s per request)

**Ready to try?** Run: `python scripts/test_ai_census_helper.py`



