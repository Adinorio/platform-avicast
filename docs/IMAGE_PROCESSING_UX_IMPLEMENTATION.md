# Image Processing UX/UI Implementation Guide

## 📋 Overview

This guide provides specific UX/UI implementation details for AVICAST's image processing workflow. Each component includes design specifications, code examples, and accessibility requirements.

**Reference**: IMAGE_PROCESSING_USER_STORIES.md, AGENTS.md §Code Style, §File Organization

---

## 🎨 Design System

### **Color Palette**

```css
/* Primary Actions */
--color-primary: #1f2937;        /* Navy blue */
--color-primary-hover: #111827;  /* Darker navy */
--color-primary-light: #374151;  /* Light navy */

/* Status Colors */
--color-success: #10b981;        /* Green - Approved */
--color-warning: #f59e0b;        /* Yellow - Pending */
--color-danger: #ef4444;         /* Red - Rejected */
--color-info: #3b82f6;           /* Blue - Processing */

/* Confidence Levels */
--confidence-high: #10b981;      /* >80% - Green */
--confidence-medium: #f59e0b;    /* 60-80% - Yellow */
--confidence-low: #ef4444;       /* <60% - Red */

/* Neutral Colors */
--color-gray-50: #f9fafb;
--color-gray-100: #f3f4f6;
--color-gray-200: #e5e7eb;
--color-gray-300: #d1d5db;
--color-gray-600: #4b5563;
--color-gray-700: #374151;
--color-gray-800: #1f2937;
```

### **Typography Scale**

```css
/* Font Family */
--font-base: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;

/* Font Sizes */
--text-xs: 0.75rem;    /* 12px */
--text-sm: 0.875rem;   /* 14px */
--text-base: 1rem;     /* 16px */
--text-lg: 1.125rem;   /* 18px */
--text-xl: 1.25rem;    /* 20px */
--text-2xl: 1.5rem;    /* 24px */
--text-3xl: 1.875rem;  /* 30px */

/* Font Weights */
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

### **Spacing System**

```css
/* 8px Base Unit */
--space-1: 0.25rem;   /* 4px */
--space-2: 0.5rem;    /* 8px */
--space-3: 0.75rem;   /* 12px */
--space-4: 1rem;      /* 16px */
--space-5: 1.25rem;   /* 20px */
--space-6: 1.5rem;    /* 24px */
--space-8: 2rem;      /* 32px */
--space-10: 2.5rem;   /* 40px */
--space-12: 3rem;     /* 48px */
```

---

## 🧩 Component Library

### **1. Image Upload Zone**

#### Visual Design
```html
<div class="upload-zone">
  <div class="upload-content">
    <i class="fas fa-cloud-upload-alt fa-3x text-gray-400"></i>
    <h3 class="mt-4 text-lg font-semibold">Drag & drop images here</h3>
    <p class="mt-2 text-sm text-gray-600">or click to browse</p>
    <p class="mt-1 text-xs text-gray-500">Supports: JPG, JPEG, PNG (Max 10MB each)</p>
  </div>
  <input type="file" class="upload-input" multiple accept="image/jpeg,image/jpg,image/png">
</div>
```

#### CSS Styling
```css
.upload-zone {
  min-height: 300px;
  border: 2px dashed var(--color-gray-300);
  border-radius: 0.5rem;
  background: var(--color-gray-50);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.upload-zone:hover {
  border-color: var(--color-info);
  background: #eff6ff;
}

.upload-zone.drag-over {
  border-color: var(--color-primary);
  background: #f0f9ff;
  border-width: 3px;
}

.upload-content {
  text-align: center;
  padding: 2rem;
}

.upload-input {
  display: none;
}
```

#### JavaScript Interaction
```javascript
const uploadZone = document.querySelector('.upload-zone');
const uploadInput = document.querySelector('.upload-input');

// Click to upload
uploadZone.addEventListener('click', () => uploadInput.click());

// Drag and drop
uploadZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  uploadZone.classList.add('drag-over');
});

uploadZone.addEventListener('dragleave', () => {
  uploadZone.classList.remove('drag-over');
});

uploadZone.addEventListener('drop', (e) => {
  e.preventDefault();
  uploadZone.classList.remove('drag-over');
  const files = e.dataTransfer.files;
  handleFileUpload(files);
});

// File selection
uploadInput.addEventListener('change', (e) => {
  handleFileUpload(e.target.files);
});
```

#### Accessibility
```html
<div class="upload-zone" 
     role="button" 
     tabindex="0"
     aria-label="Upload bird images. Drag and drop or press Enter to browse">
  <!-- content -->
</div>
```

---

### **2. Image Preview Cards (Process Page)**

#### Visual Design
```html
<div class="image-card">
  <div class="image-preview">
    <img src="thumbnail.jpg" alt="Bird image - Site A Morning Survey" loading="lazy">
    <span class="status-badge captured">CAPTURED</span>
  </div>
  <div class="card-body">
    <h6 class="card-title">Site A - Morning Survey</h6>
    <p class="card-meta">
      <span class="file-size">2.5 MB</span>
      <span class="separator">•</span>
      <span class="upload-time">5 min ago</span>
    </p>
    <div class="card-actions">
      <button class="btn btn-primary process-btn" data-image-id="uuid">
        <i class="fas fa-search"></i> Clarify with AI
      </button>
      <button class="btn btn-secondary skip-btn" onclick="skipProcessing('uuid')">
        <i class="fas fa-clock"></i> Process Later
      </button>
    </div>
  </div>
</div>
```

#### CSS Styling
```css
.image-card {
  background: white;
  border-radius: 0.5rem;
  overflow: hidden;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
  transition: box-shadow 0.3s ease, transform 0.3s ease;
}

.image-card:hover {
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.image-preview {
  position: relative;
  width: 100%;
  height: 200px;
  overflow: hidden;
  background: var(--color-gray-100);
}

.image-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.status-badge {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  text-transform: uppercase;
}

.status-badge.captured {
  background: var(--color-info);
  color: white;
}

.card-body {
  padding: 1rem;
}

.card-title {
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  color: var(--color-gray-800);
  margin-bottom: 0.5rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-meta {
  font-size: var(--text-sm);
  color: var(--color-gray-600);
  margin-bottom: 1rem;
}

.separator {
  margin: 0 0.5rem;
}

.card-actions {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.btn {
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.btn-primary {
  background: #f59e0b;  /* Warning yellow */
  color: white;
}

.btn-primary:hover {
  background: #d97706;
}

.btn-secondary {
  background: transparent;
  color: var(--color-gray-700);
  border: 1px solid var(--color-gray-300);
}

.btn-secondary:hover {
  background: var(--color-gray-50);
}
```

---

### **3. Processing Progress Bar**

#### Visual Design
```html
<div class="processing-container">
  <div class="processing-header">
    <h5>Processing: "Site A - Morning Survey"</h5>
    <button class="btn-icon" onclick="cancelProcessing()">
      <i class="fas fa-times"></i>
    </button>
  </div>
  
  <div class="progress-wrapper">
    <div class="progress-bar">
      <div class="progress-fill" style="width: 60%" role="progressbar" aria-valuenow="60" aria-valuemin="0" aria-valuemax="100">
        <span class="progress-text">60%</span>
      </div>
    </div>
  </div>
  
  <p class="progress-message">
    <i class="fas fa-spinner fa-spin"></i>
    <span>Detecting birds...</span>
  </p>
  
  <p class="progress-estimate">Estimated time: ~5 seconds</p>
</div>
```

#### CSS Styling
```css
.processing-container {
  background: white;
  border-radius: 0.5rem;
  padding: 1.5rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.processing-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.processing-header h5 {
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--color-gray-800);
}

.btn-icon {
  background: transparent;
  border: none;
  color: var(--color-gray-600);
  cursor: pointer;
  padding: 0.5rem;
}

.btn-icon:hover {
  color: var(--color-gray-800);
}

.progress-wrapper {
  margin-bottom: 1rem;
}

.progress-bar {
  width: 100%;
  height: 2rem;
  background: var(--color-gray-200);
  border-radius: 9999px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #2563eb);
  background-size: 200% 100%;
  animation: progressShine 2s infinite;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: width 0.5s ease;
}

@keyframes progressShine {
  0% { background-position: 200% center; }
  100% { background-position: -200% center; }
}

.progress-text {
  color: white;
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
}

.progress-message {
  font-size: var(--text-base);
  color: var(--color-gray-700);
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.progress-estimate {
  font-size: var(--text-sm);
  color: var(--color-gray-600);
}
```

---

### **4. Review Result Card with Bounding Box**

#### Visual Design
```html
<div class="review-result-card">
  <div class="image-section">
    <div class="image-container">
      <img src="/api/image-with-bbox/uuid" 
           id="review-image-uuid" 
           alt="Chinese Egret detection"
           data-original-url="/media/original.jpg">
    </div>
    
    <div class="image-controls">
      <div class="btn-group">
        <button class="btn-toggle active" onclick="toggleView('uuid', 'bbox')">
          <i class="fas fa-search-plus"></i> Box
        </button>
        <button class="btn-toggle" onclick="toggleView('uuid', 'original')">
          <i class="fas fa-image"></i> Original
        </button>
      </div>
    </div>
  </div>
  
  <div class="info-section">
    <div class="detection-header">
      <div>
        <h4 class="species-name">Chinese Egret</h4>
        <p class="species-scientific">Egretta eulophotes</p>
      </div>
      <span class="confidence-badge high">92%</span>
    </div>
    
    <div class="detection-meta">
      <div class="meta-item">
        <i class="fas fa-check-circle"></i>
        <span>3 detections total</span>
      </div>
      <div class="meta-item">
        <i class="fas fa-clock"></i>
        <span>Processed 2 min ago</span>
      </div>
      <div class="meta-item">
        <i class="fas fa-robot"></i>
        <span>Model: egret_500_v1</span>
      </div>
    </div>
    
    <div class="action-buttons">
      <button class="btn btn-approve" data-result-id="uuid" data-action="approve">
        <i class="fas fa-check"></i> Approve
      </button>
      <button class="btn btn-reject" data-result-id="uuid" data-action="reject">
        <i class="fas fa-times"></i> Reject
      </button>
      <button class="btn btn-override" data-result-id="uuid" data-action="override">
        <i class="fas fa-edit"></i> Override
      </button>
      <button class="btn btn-skip" data-result-id="uuid" data-action="skip">
        <i class="fas fa-clock"></i> Review Later
      </button>
    </div>
    
    <div class="keyboard-hints">
      <span class="hint">A - Approve</span>
      <span class="hint">R - Reject</span>
      <span class="hint">O - Override</span>
      <span class="hint">S - Skip</span>
    </div>
  </div>
</div>
```

#### CSS Styling
```css
.review-result-card {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  background: white;
  border-radius: 0.5rem;
  padding: 1.5rem;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
}

.image-section {
  position: relative;
}

.image-container {
  width: 100%;
  min-height: 400px;
  background: var(--color-gray-100);
  border-radius: 0.5rem;
  overflow: hidden;
}

.image-container img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.image-controls {
  position: absolute;
  top: 1rem;
  right: 1rem;
}

.btn-group {
  display: flex;
  gap: 0.25rem;
  background: white;
  border-radius: 0.375rem;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
}

.btn-toggle {
  padding: 0.5rem 1rem;
  background: transparent;
  border: none;
  cursor: pointer;
  color: var(--color-gray-700);
  font-size: var(--text-sm);
  transition: all 0.2s ease;
}

.btn-toggle.active {
  background: var(--color-primary);
  color: white;
}

.btn-toggle:hover:not(.active) {
  background: var(--color-gray-100);
}

.info-section {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.detection-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.species-name {
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
  color: var(--color-gray-800);
  margin-bottom: 0.25rem;
}

.species-scientific {
  font-size: var(--text-base);
  font-style: italic;
  color: var(--color-gray-600);
}

.confidence-badge {
  padding: 0.5rem 1rem;
  border-radius: 9999px;
  font-size: var(--text-lg);
  font-weight: var(--font-bold);
}

.confidence-badge.high {
  background: #d1fae5;
  color: #065f46;
}

.confidence-badge.medium {
  background: #fef3c7;
  color: #92400e;
}

.confidence-badge.low {
  background: #fee2e2;
  color: #991b1b;
}

.detection-meta {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--color-gray-600);
  font-size: var(--text-sm);
}

.meta-item i {
  color: var(--color-gray-400);
}

.action-buttons {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}

.btn-approve {
  background: var(--color-success);
  color: white;
}

.btn-approve:hover {
  background: #059669;
}

.btn-reject {
  background: var(--color-danger);
  color: white;
}

.btn-reject:hover {
  background: #dc2626;
}

.btn-override {
  background: var(--color-warning);
  color: white;
}

.btn-override:hover {
  background: #d97706;
}

.btn-skip {
  background: transparent;
  color: var(--color-gray-700);
  border: 1px solid var(--color-gray-300);
}

.btn-skip:hover {
  background: var(--color-gray-50);
}

.keyboard-hints {
  display: flex;
  gap: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--color-gray-200);
}

.hint {
  font-size: var(--text-xs);
  color: var(--color-gray-500);
  background: var(--color-gray-100);
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-family: monospace;
}

/* Responsive */
@media (max-width: 1024px) {
  .review-result-card {
    grid-template-columns: 1fr;
  }
  
  .action-buttons {
    grid-template-columns: 1fr;
  }
}
```

---

### **5. Override Modal**

#### Visual Design
```html
<div class="modal-overlay" id="override-modal">
  <div class="modal-container">
    <div class="modal-header">
      <h3>Override Species Detection</h3>
      <button class="btn-close" onclick="closeModal()">
        <i class="fas fa-times"></i>
      </button>
    </div>
    
    <div class="modal-body">
      <p class="modal-description">
        AI detected: <strong>Little Egret (85%)</strong>
        <br>Select the correct species:
      </p>
      
      <div class="species-grid">
        <label class="species-option">
          <input type="radio" name="species" value="Chinese_Egret">
          <div class="species-card">
            <img src="/static/species/chinese-egret.jpg" alt="Chinese Egret">
            <span class="species-name">Chinese Egret</span>
          </div>
        </label>
        
        <label class="species-option">
          <input type="radio" name="species" value="Great_Egret">
          <div class="species-card">
            <img src="/static/species/great-egret.jpg" alt="Great Egret">
            <span class="species-name">Great Egret</span>
          </div>
        </label>
        
        <!-- 4 more species options -->
      </div>
      
      <div class="form-group">
        <label for="override-reason">Reason (optional)</label>
        <textarea id="override-reason" 
                  rows="3" 
                  placeholder="e.g., Larger size, yellow bill, different markings..."
                  maxlength="200"></textarea>
        <span class="char-counter">0/200</span>
      </div>
    </div>
    
    <div class="modal-footer">
      <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
      <button class="btn btn-primary" onclick="saveOverride()">Save Override</button>
    </div>
  </div>
</div>
```

#### CSS Styling
```css
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: none;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease;
}

.modal-overlay.active {
  display: flex;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal-container {
  background: white;
  border-radius: 0.5rem;
  width: 90%;
  max-width: 700px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid var(--color-gray-200);
}

.modal-header h3 {
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  color: var(--color-gray-800);
}

.btn-close {
  background: transparent;
  border: none;
  color: var(--color-gray-600);
  cursor: pointer;
  padding: 0.5rem;
  font-size: 1.25rem;
}

.btn-close:hover {
  color: var(--color-gray-800);
}

.modal-body {
  padding: 1.5rem;
}

.modal-description {
  color: var(--color-gray-700);
  margin-bottom: 1.5rem;
}

.species-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.species-option {
  cursor: pointer;
}

.species-option input[type="radio"] {
  display: none;
}

.species-card {
  border: 2px solid var(--color-gray-200);
  border-radius: 0.5rem;
  padding: 1rem;
  text-align: center;
  transition: all 0.2s ease;
}

.species-option input:checked + .species-card {
  border-color: var(--color-primary);
  background: #f0f9ff;
}

.species-card:hover {
  border-color: var(--color-gray-400);
}

.species-card img {
  width: 100%;
  height: 100px;
  object-fit: cover;
  border-radius: 0.375rem;
  margin-bottom: 0.5rem;
}

.species-name {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--color-gray-800);
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--color-gray-700);
  margin-bottom: 0.5rem;
}

.form-group textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid var(--color-gray-300);
  border-radius: 0.375rem;
  font-size: var(--text-sm);
  font-family: var(--font-base);
  resize: vertical;
}

.form-group textarea:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.char-counter {
  display: block;
  text-align: right;
  font-size: var(--text-xs);
  color: var(--color-gray-500);
  margin-top: 0.25rem;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1.5rem;
  border-top: 1px solid var(--color-gray-200);
}
```

---

### **6. Empty States**

#### No Images to Process
```html
<div class="empty-state">
  <div class="empty-icon">
    <i class="fas fa-images fa-4x"></i>
  </div>
  <h3 class="empty-title">No Images Ready for Processing</h3>
  <p class="empty-description">
    Upload bird images to start the AI detection workflow.
  </p>
  <a href="/image-processing/upload/" class="btn btn-primary">
    <i class="fas fa-upload"></i> Upload Images
  </a>
</div>
```

#### No Results Pending Review
```html
<div class="empty-state">
  <div class="empty-icon">
    <i class="fas fa-check-circle fa-4x"></i>
  </div>
  <h3 class="empty-title">All Caught Up!</h3>
  <p class="empty-description">
    No results pending review. Great work!
  </p>
  <a href="/image-processing/process/" class="btn btn-primary">
    Process More Images
  </a>
</div>
```

#### CSS Styling
```css
.empty-state {
  text-align: center;
  padding: 4rem 2rem;
}

.empty-icon {
  color: var(--color-gray-300);
  margin-bottom: 1.5rem;
}

.empty-title {
  font-size: var(--text-2xl);
  font-weight: var(--font-semibold);
  color: var(--color-gray-800);
  margin-bottom: 0.75rem;
}

.empty-description {
  font-size: var(--text-base);
  color: var(--color-gray-600);
  margin-bottom: 1.5rem;
  max-width: 500px;
  margin-left: auto;
  margin-right: auto;
}
```

---

### **7. Toast Notifications**

#### Visual Design
```html
<div class="toast-container">
  <div class="toast toast-success">
    <div class="toast-icon">
      <i class="fas fa-check-circle"></i>
    </div>
    <div class="toast-content">
      <h6 class="toast-title">Success</h6>
      <p class="toast-message">Image approved successfully</p>
    </div>
    <button class="toast-close">
      <i class="fas fa-times"></i>
    </button>
  </div>
</div>
```

#### CSS Styling
```css
.toast-container {
  position: fixed;
  top: 1rem;
  right: 1rem;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.toast {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: white;
  border-radius: 0.5rem;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  min-width: 300px;
  animation: slideInRight 0.3s ease;
}

@keyframes slideInRight {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.toast-success {
  border-left: 4px solid var(--color-success);
}

.toast-error {
  border-left: 4px solid var(--color-danger);
}

.toast-warning {
  border-left: 4px solid var(--color-warning);
}

.toast-info {
  border-left: 4px solid var(--color-info);
}

.toast-icon {
  font-size: 1.5rem;
}

.toast-success .toast-icon {
  color: var(--color-success);
}

.toast-content {
  flex: 1;
}

.toast-title {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--color-gray-800);
  margin-bottom: 0.25rem;
}

.toast-message {
  font-size: var(--text-sm);
  color: var(--color-gray-600);
}

.toast-close {
  background: transparent;
  border: none;
  color: var(--color-gray-400);
  cursor: pointer;
  padding: 0.25rem;
}

.toast-close:hover {
  color: var(--color-gray-600);
}
```

#### JavaScript Helper
```javascript
function showToast(type, title, message, duration = 3000) {
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <div class="toast-icon">
      <i class="fas fa-${type === 'success' ? 'check-circle' : 
                         type === 'error' ? 'exclamation-circle' :
                         type === 'warning' ? 'exclamation-triangle' : 'info-circle'}"></i>
    </div>
    <div class="toast-content">
      <h6 class="toast-title">${title}</h6>
      <p class="toast-message">${message}</p>
    </div>
    <button class="toast-close" onclick="this.parentElement.remove()">
      <i class="fas fa-times"></i>
    </button>
  `;
  
  document.querySelector('.toast-container').appendChild(toast);
  
  setTimeout(() => {
    toast.style.animation = 'slideOutRight 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// Usage
showToast('success', 'Approved', 'Image approved successfully');
showToast('error', 'Error', 'Failed to process image');
```

---

## 📱 Responsive Design

### Breakpoint Strategy
```css
/* Mobile First Approach */
.image-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
}

/* Tablet: 768px+ */
@media (min-width: 768px) {
  .image-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* Desktop: 1024px+ */
@media (min-width: 1024px) {
  .image-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

/* Large Desktop: 1280px+ */
@media (min-width: 1280px) {
  .image-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}
```

---

## ♿ Accessibility Requirements

### ARIA Labels
```html
<button class="btn-approve" 
        aria-label="Approve detection for Chinese Egret with 92% confidence">
  Approve
</button>
```

### Keyboard Navigation
```javascript
// Review page keyboard shortcuts
document.addEventListener('keydown', (e) => {
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
  
  switch(e.key.toLowerCase()) {
    case 'a':
      document.querySelector('[data-action="approve"]')?.click();
      break;
    case 'r':
      document.querySelector('[data-action="reject"]')?.click();
      break;
    case 'o':
      document.querySelector('[data-action="override"]')?.click();
      break;
    case 's':
      document.querySelector('[data-action="skip"]')?.click();
      break;
  }
});
```

### Focus Management
```css
/* Visible focus indicators */
button:focus, 
input:focus, 
select:focus, 
textarea:focus {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

/* Skip to content link */
.skip-link {
  position: absolute;
  top: -40px;
  left: 0;
  background: var(--color-primary);
  color: white;
  padding: 0.5rem 1rem;
  z-index: 100;
}

.skip-link:focus {
  top: 0;
}
```

---

## 🚀 Implementation Checklist

### Phase 1: Foundation ✅
- [x] Color system defined
- [x] Typography scale established
- [x] Spacing system implemented
- [x] Base components created

### Phase 2: Core Components 🔄
- [x] Upload zone
- [x] Image cards
- [x] Progress bars
- [x] Review cards
- [ ] Override modal
- [ ] Toast notifications

### Phase 3: Interactions 📋
- [ ] Drag and drop
- [ ] Keyboard shortcuts
- [ ] Batch selection
- [ ] Undo/redo actions

### Phase 4: Polish 📋
- [ ] Animations
- [ ] Transitions
- [ ] Empty states
- [ ] Error states
- [ ] Loading states

### Phase 5: Accessibility 📋
- [ ] ARIA labels
- [ ] Keyboard navigation
- [ ] Focus management
- [ ] Screen reader testing
- [ ] Color contrast audit

---

**🎯 Implementation Priority**: Focus on core user flows first (Upload → Process → Review → Allocate), then enhance with advanced interactions and accessibility features.

**Reference**: See IMAGE_PROCESSING_USER_STORIES.md for user scenarios, AGENTS.md §Code Style for implementation standards.




