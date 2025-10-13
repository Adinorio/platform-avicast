# AI Census Helper - Quick Start

## ⚡ 5-Minute Setup

### 1. Install Ollama

**Windows:**
- Download: https://ollama.com/download/windows
- Run installer
- Restart terminal

**Verify:**
```bash
ollama --version
```

---

### 2. Download a Model (Pick One)

```bash
# Option A: Fast & efficient (Recommended)
ollama pull llama3.2

# Option B: More accurate
ollama pull mistral

# Option C: Balanced
ollama pull phi3
```

**Wait time:** 2-5 minutes (downloads 3-7GB)

---

### 3. Test AI Integration

```bash
python scripts/test_ai_census_helper.py
```

**Expected Output:**
```
✅ AI Assistant is available!
   Model: llama3.2
   Endpoint: http://localhost:11434
```

---

## 🎯 What You Can Do

### 1. **Species Name Matching**
User types: "chinese egret" → AI matches to "Chinese Egret"

### 2. **Data Validation**
AI warns: "Count of 10,000 seems unusually high for this species"

### 3. **Smart Error Fixes**
AI suggests: "Did you mean 'Black-faced Spoonbill' instead of 'Black Spoonbill'?"

### 4. **Friendly Summaries**
AI: "Great! Imported 145/150 observations. 5 skipped due to species name mismatches."

---

## 📊 Performance

| Model | Speed | Accuracy | Size |
|-------|-------|----------|------|
| llama3.2 | ⚡⚡⚡ | ⭐⭐⭐ | 3GB |
| mistral | ⚡⚡ | ⭐⭐⭐⭐ | 7GB |
| phi3 | ⚡⚡⚡ | ⭐⭐⭐ | 4GB |

**Recommendation:** Start with `llama3.2`

---

## 🔒 Privacy & Security

✅ **100% Offline** - No internet after setup  
✅ **Local Processing** - Data never leaves your computer  
✅ **AGENTS.md Compliant** - Local-first deployment  
✅ **No External APIs** - Fully self-contained

---

## 🚀 Try It Now!

**Step 1:** Install Ollama (2 minutes)  
**Step 2:** Pull model (3 minutes)  
**Step 3:** Run test script (30 seconds)  

**Total Time:** ~5 minutes

**Full Guide:** See `docs/AI_CENSUS_HELPER_GUIDE.md`

---

## ❓ Troubleshooting

**Problem:** "AI unavailable"  
**Fix:** Run `ollama pull llama3.2`

**Problem:** "Ollama not found"  
**Fix:** Install from https://ollama.com/download

**Problem:** "Slow responses"  
**Fix:** Use `llama3.2` instead of `mistral`

---

**Ready?** Install Ollama and run the test! 🎉


