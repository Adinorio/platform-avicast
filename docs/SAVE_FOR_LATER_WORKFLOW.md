# 📋 "Save for Later" Workflow Guide

## Overview
AVICAST's GTD-based workflow allows users to **defer decisions at every stage**, ensuring flexible processing without losing data.

---

## 🔄 Complete Workflow with "Save for Later" Options

### **1️⃣ CAPTURE Stage (Upload)**
**Location**: `/image-processing/upload/`

**Default Behavior**:
- ✅ All uploaded images automatically saved with status "CAPTURED"
- ✅ No time limit - images remain until you process them
- ✅ No action needed to "save for later" - it's automatic!

**What Happens**:
- Image stored in database
- Status: `CAPTURED`
- Appears in Process page whenever you're ready

---

### **2️⃣ CLARIFY Stage (Process with AI)**
**Location**: `/image-processing/process/`

**Options Available**:
1. **Clarify with AI** (Yellow button) - Process image now with AI detection
2. **Process Later** (Gray button) - Skip this image for now ✨ NEW!

**"Process Later" Behavior**:
- ✅ Hides image from current view (visual feedback)
- ✅ Image stays in `CAPTURED` status
- ✅ Will reappear next time you visit the Process page
- ✅ No data loss - image remains in system

**Use Cases**:
- Unsure about image quality
- Want to prioritize other images first
- Need to consult with team before processing
- Batch processing - come back later

---

### **3️⃣ ORGANIZE Stage (Results Ready)**
**Location**: `/image-processing/list/`

**Automatic Behavior**:
- ✅ Processed images automatically saved with status "ORGANIZED"
- ✅ Results stored in database
- ✅ Ready for review whenever convenient

---

### **4️⃣ REFLECT Stage (Review AI Results)**
**Location**: `/image-processing/review/`

**Options Available**:
1. **Approve** (Green button) - Accept AI detection
2. **Reject** (Red button) - Reject detection
3. **Override** (Yellow button) - Manual correction
4. **Review Later** (Gray button) - Skip review for now

**"Review Later" Behavior**:
- ✅ Result stays in `PENDING` status
- ✅ Reappears in review queue
- ✅ AI detection results preserved
- ✅ Can review anytime

**Use Cases**:
- Need expert opinion before deciding
- Unclear species identification
- Want to compare with similar images
- Defer decision pending more data

---

### **5️⃣ ENGAGE Stage (Allocate to Census)**
**Location**: `/image-processing/allocate/`

**Options Available**:
1. **Allocate to Site** - Assign to census location
2. **Skip Allocation** - Defer allocation

**"Skip Allocation" Behavior**:
- ✅ Result stays approved but unallocated
- ✅ Reappears in allocation queue
- ✅ Can allocate from dashboard later
- ✅ No data loss

**Use Cases**:
- Uncertain about correct site
- Waiting for site creation
- Need to verify location coordinates
- Batch allocation preferred

---

## 📊 Workflow Status Tracking

| Stage | Status | "Save for Later" Option | Next Appearance |
|-------|--------|------------------------|-----------------|
| CAPTURE | `CAPTURED` | Automatic | Process page |
| CLARIFY | `CAPTURED` | "Process Later" button | Process page (next visit) |
| ORGANIZE | `ORGANIZED` | Automatic | Review page |
| REFLECT | `PENDING` | "Review Later" button | Review page |
| ENGAGE | `APPROVED` (unallocated) | "Skip Allocation" | Allocate page/Dashboard |

---

## 🎯 Key Benefits

### **Flexibility**
- No forced decisions
- Work at your own pace
- Prioritize critical images first

### **Data Integrity**
- Nothing gets lost
- All images tracked in database
- Complete audit trail

### **GTD Methodology**
- Capture everything first
- Process when ready
- Review thoughtfully
- Engage appropriately

---

## 💡 Best Practices

### **1. Batch Processing**
```
1. Upload all images (CAPTURE)
2. Skip uncertain ones (Process Later)
3. Process clear images first
4. Return to skipped images with more context
```

### **2. Quality Control**
```
1. Process all images (CLARIFY)
2. Review high-confidence detections first (REFLECT)
3. Skip low-confidence for expert review (Review Later)
4. Batch-allocate approved results (ENGAGE)
```

### **3. Collaborative Workflow**
```
Field Worker:
  - Uploads images (CAPTURE)
  - Skips unclear images (Process Later)

Admin:
  - Reviews all results (REFLECT)
  - Overrides incorrect detections
  - Allocates to census (ENGAGE)

Superadmin:
  - Final quality check
  - Handles edge cases
  - System oversight
```

---

## 🔍 Finding Saved Items

### **Dashboard Overview**
Visit `/image-processing/` to see:
- Total images by status
- Pending reviews count
- Unallocated results
- Recent activity

### **Filter by Stage**
Use the List view: `/image-processing/list/?stage=captured`
- `?stage=captured` - Unprocessed images
- `?stage=organized` - Processed, pending review
- `?stage=all` - Everything

### **Search by User**
- SUPERADMIN/ADMIN: See all images
- Regular users: See only their uploads

---

## 🚀 Quick Reference

| I want to... | Action | Location |
|-------------|--------|----------|
| Save upload for later | Upload it (automatic) | Upload page |
| Skip processing now | Click "Process Later" | Process page |
| Defer review decision | Click "Review Later" | Review page |
| Postpone allocation | Click "Skip Allocation" | Allocate page |
| Find skipped images | Visit same page again | Respective stage page |
| See all pending items | Check Dashboard | Dashboard |

---

## 📝 Technical Notes

### **Database Status Flow**
```
CAPTURED → [Process Later: stays CAPTURED]
CAPTURED → [Clarify with AI] → ORGANIZED
ORGANIZED → [Review Later: stays PENDING] 
ORGANIZED → [Approve/Reject] → REFLECTED
REFLECTED → [Skip Allocation: stays REFLECTED]
REFLECTED → [Allocate] → ENGAGED
```

### **Frontend Implementation**
- "Process Later" button uses fade animation
- Hides card from current view (UI only)
- Backend status unchanged (stays CAPTURED)
- Image reappears on page refresh

### **Future Enhancements**
- Add "deferred" flag for priority sorting
- Email reminders for long-pending items
- Bulk skip/defer operations
- Custom defer reasons/notes

---

**Remember**: AVICAST follows GTD principles - **capture everything, then decide later**. The "Save for Later" options ensure you never lose data while maintaining workflow flexibility! 🎉




