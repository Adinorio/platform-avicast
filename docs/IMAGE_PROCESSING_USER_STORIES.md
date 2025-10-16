# Image Processing Workflow - User Stories & Use Cases

## 📋 Executive Summary

This document defines user stories, use cases, and UX/UI requirements for AVICAST's AI-powered image processing workflow. Following GTD methodology (AGENTS.md §GTD Workflow), the system guides users through: **CAPTURE → CLARIFY → ORGANIZE → REFLECT → ENGAGE**.

**Reference**: AGENTS.md §Development Guidelines, §File Organization, §Security Checklist

---

## 👥 User Personas for Image Processing

### **Primary Users**

#### 1. **Field Worker (Maria Santos)**
- **Role**: Wildlife Monitoring Technician
- **Goals**: Quickly upload bird photos from field surveys, minimal data entry
- **Pain Points**: Limited time in field, unreliable network, needs offline capability
- **Tech Comfort**: Medium - uses smartphone/tablet primarily
- **Typical Session**: Uploads 20-50 images in batch after field visit

#### 2. **Data Analyst (Dr. Alex Kim)**
- **Role**: Conservation Biologist
- **Goals**: Review AI detections for accuracy, override incorrect classifications
- **Pain Points**: AI errors waste time, needs confidence in results before census allocation
- **Tech Comfort**: High - expects detailed metadata, validation tools
- **Typical Session**: Reviews 100+ images daily, focuses on quality control

#### 3. **Site Manager (Carlos Rivera)**
- **Role**: Regional Conservation Officer
- **Goals**: Allocate approved detections to census sites, generate reports
- **Pain Points**: Needs to match images to correct sites, verify location accuracy
- **Tech Comfort**: Medium - prefers visual interfaces, clear workflows
- **Typical Session**: Allocates 50-100 processed images to multiple sites

#### 4. **System Administrator (Linda Chen)**
- **Role**: IT/Database Administrator
- **Goals**: Monitor system performance, manage AI models, troubleshoot issues
- **Pain Points**: Needs visibility into processing queue, error handling
- **Tech Comfort**: Very High - expects advanced controls, logs, metrics
- **Typical Session**: System maintenance, model updates, user support

---

## 📖 User Stories

### **Stage 1: CAPTURE (Upload Images)**

#### Story 1.1: Bulk Image Upload
```
As a Field Worker,
I want to upload multiple bird images at once from my field survey,
So that I can efficiently transfer all photos without repetitive clicking.

Acceptance Criteria:
✅ Drag-and-drop interface accepts multiple files
✅ Shows upload progress for each file
✅ Supports JPG, JPEG, PNG formats only
✅ Clear error messages for invalid files
✅ Preview thumbnails before submission
✅ Batch title option (e.g., "Site A - Morning Survey")
✅ Optional site hint field for easier allocation later
✅ Upload completes in <5 seconds for 10 images
✅ Success confirmation with uploaded count

UX Requirements:
- Large drop zone (min 300px height)
- Visual feedback on hover/drag
- File count indicator
- Remove file option before upload
- Mobile-friendly interface
```

#### Story 1.2: Upload with Metadata
```
As a Field Worker,
I want to add location hints and titles during upload,
So that images can be easily allocated to census sites later.

Acceptance Criteria:
✅ Optional "Site Hint" field with auto-complete
✅ Title field with smart defaults (date + location)
✅ File size displayed for each image
✅ Original filename preserved in system
✅ Metadata saved with each ImageUpload record

UX Requirements:
- Auto-complete suggests recent sites
- Character counter for title (max 200)
- File size shown in MB/KB
- Clear labeling of required vs optional fields
```

#### Story 1.3: Upload Error Handling
```
As a Field Worker,
I want clear feedback when uploads fail,
So that I can fix issues without losing my work.

Acceptance Criteria:
✅ File size limit clearly stated (e.g., "Max 10MB per image")
✅ Invalid format shows specific error
✅ Network errors provide retry option
✅ Partial uploads preserved (retry only failed files)
✅ Error summary at end of batch upload

UX Requirements:
- Red error badges on failed files
- "Retry Failed" button
- Download failed files list
- Help link to troubleshooting guide
```

---

### **Stage 2: CLARIFY (Process with AI)**

#### Story 2.1: AI Processing Queue
```
As a Field Worker,
I want to see all my unprocessed images in one view,
So that I can decide which ones to process immediately.

Acceptance Criteria:
✅ Grid view shows image thumbnails (200x200px)
✅ Image title, upload time, file size displayed
✅ Two action buttons: "Clarify with AI" + "Process Later"
✅ Images sorted by upload date (newest first)
✅ Visual indicator for processing status (badges)
✅ ADMIN/SUPERADMIN see all users' images
✅ Regular users see only their own uploads

UX Requirements:
- 3-4 columns grid on desktop
- Hover effects on image cards
- Smooth fade animation for "Process Later"
- Status badge color: Blue = CAPTURED
```

#### Story 2.2: AI Processing Feedback
```
As a Field Worker,
I want to see real-time progress when AI processes my image,
So that I know the system is working and estimate wait time.

Acceptance Criteria:
✅ Progress bar with percentage (0-100%)
✅ Status messages: "Loading model", "Analyzing", "Detecting", "Finalizing"
✅ Processing time estimate
✅ Animated progress bar (striped, moving)
✅ Processing completes in <10 seconds per image
✅ Success notification with detection summary

UX Requirements:
- Full-width progress bar
- Large, readable status text
- Green checkmark on completion
- Auto-redirect to review page option
```

#### Story 2.3: Defer Processing Decision
```
As a Field Worker,
I want to skip unclear images and process them later,
So that I can focus on high-quality photos first.

Acceptance Criteria:
✅ "Process Later" button visible on each image card
✅ Clicking button hides image with fade animation
✅ Image stays in CAPTURED status
✅ Confirmation message shown
✅ Image reappears on next visit to process page

UX Requirements:
- Gray/secondary colored button
- Clock icon indicator
- Smooth opacity transition (300ms)
- Toast notification: "Saved for later"
```

#### Story 2.4: Batch Processing
```
As a Data Analyst,
I want to process multiple images at once,
So that I can efficiently handle large datasets.

Acceptance Criteria:
✅ "Select All" checkbox at top of grid
✅ Individual checkboxes on each image card
✅ "Process Selected" button (disabled if none selected)
✅ Batch progress indicator
✅ Sequential processing with queue status
✅ Pause/Cancel batch option

UX Requirements:
- Selected images have blue border
- Batch counter: "5 selected"
- Queue list shows processing order
- Stop button with confirmation dialog
```

---

### **Stage 3: ORGANIZE (View Results)**

#### Story 3.1: Browse Processed Images
```
As a Data Analyst,
I want to browse all processed images by workflow stage,
So that I can find images needing review, allocation, etc.

Acceptance Criteria:
✅ Filter tabs: All | Captured | Clarified | Organized | Reflected | Engaged
✅ Count badges on each filter tab
✅ Grid view with thumbnails
✅ Sort options: Date, Confidence, Species
✅ Pagination (20 images per page)
✅ Search by title or filename

UX Requirements:
- Active tab highlighted (blue background)
- Count badges with subtle background
- Sort dropdown in top-right corner
- Clear pagination controls
- Search bar with icon
```

---

### **Stage 4: REFLECT (Review AI Results)**

#### Story 4.1: Review Detection Results
```
As a Data Analyst,
I want to review AI detections with bounding boxes and confidence scores,
So that I can validate accuracy before allocating to census data.

Acceptance Criteria:
✅ Image displayed with AI-drawn bounding box
✅ Detected species name prominently shown
✅ Confidence score as percentage (e.g., "85%")
✅ Toggle between bounding box and original image
✅ Total detections count if multiple birds
✅ Detection timestamp and AI model version
✅ Four action buttons: Approve | Reject | Override | Review Later

UX Requirements:
- Large image preview (min 400px width)
- Red bounding box with 3px border
- Species label above bounding box
- Toggle buttons: "Box" (active) | "Original"
- Confidence color-coded: Green (>80%), Yellow (60-80%), Red (<60%)
```

#### Story 4.2: Approve/Reject Workflow
```
As a Data Analyst,
I want to quickly approve or reject AI detections,
So that I can process large review queues efficiently.

Acceptance Criteria:
✅ Green "Approve" button marks detection as correct
✅ Red "Reject" button marks detection as incorrect
✅ Keyboard shortcuts: A (approve), R (reject), O (override), S (skip)
✅ Action confirmation with toast notification
✅ Auto-advance to next pending result
✅ Undo last action option (5-second window)
✅ Review progress indicator (e.g., "3 of 15 reviewed")

UX Requirements:
- Large, touch-friendly buttons (min 100px width)
- Keyboard shortcuts shown in tooltips
- Toast notifications in top-right
- Undo button with countdown timer
- Progress bar at top of page
```

#### Story 4.3: Override Incorrect Detection
```
As a Data Analyst,
I want to manually override incorrect AI species classifications,
So that census data reflects accurate identifications.

Acceptance Criteria:
✅ "Override" button opens species selection modal
✅ Modal shows all 6 egret species as options
✅ Species displayed with images for visual confirmation
✅ Override reason field (optional text)
✅ Save override updates species and marks as OVERRIDDEN
✅ Override logged with user ID and timestamp

UX Requirements:
- Modal centered, 600px width
- Species grid with radio buttons
- Hover preview of species image
- "Reason" textarea (optional)
- Clear Save/Cancel buttons
```

#### Story 4.4: Defer Review Decision
```
As a Data Analyst,
I want to skip uncertain detections for expert review,
So that I can maintain quality without blocking workflow.

Acceptance Criteria:
✅ "Review Later" button keeps result in PENDING status
✅ Result stays in review queue
✅ Skipped count tracked per session
✅ Filter for "Skipped by me" results
✅ No penalty for deferring decisions

UX Requirements:
- Gray outline button
- Clock icon indicator
- Toast: "Deferred for later review"
- Session summary: "5 reviewed, 2 deferred"
```

#### Story 4.5: Batch Review Actions
```
As a Data Analyst,
I want to approve multiple similar detections at once,
So that I can handle repetitive reviews efficiently.

Acceptance Criteria:
✅ Checkbox selection on review cards
✅ "Approve Selected" button
✅ "Reject Selected" button
✅ Batch action confirmation dialog
✅ Undo batch action option

UX Requirements:
- Select All checkbox
- Batch action bar appears when items selected
- Confirmation shows count: "Approve 8 results?"
- Undo for 10 seconds after batch action
```

---

### **Stage 5: ENGAGE (Allocate to Census)**

#### Story 5.1: Allocate to Census Site
```
As a Site Manager,
I want to allocate approved detections to specific census sites,
So that population data is correctly attributed geographically.

Acceptance Criteria:
✅ Only APPROVED/OVERRIDDEN results shown
✅ Site dropdown with search/filter
✅ Site hint from upload shown as suggestion
✅ Map preview of selected site (if coordinates available)
✅ Census date picker with smart defaults
✅ Bulk allocation for same site

UX Requirements:
- Searchable dropdown (Select2 or similar)
- Site hint shown with badge
- Mini map preview (200x200px)
- Date picker with calendar widget
- "Apply to All" checkbox for batch allocation
```

#### Story 5.2: Skip Allocation
```
As a Site Manager,
I want to defer allocation decisions when unsure,
So that I can verify site details before committing data.

Acceptance Criteria:
✅ "Skip Allocation" button available
✅ Result stays approved but unallocated
✅ Reappears in allocation queue
✅ Filter for unallocated results
✅ Allocation dashboard shows pending count

UX Requirements:
- Secondary button style
- Confirmation message
- Dashboard widget: "15 pending allocation"
- Unallocated results highlighted in list
```

---

## 🎯 Use Case Scenarios

### **Use Case 1: Field Survey Workflow**

**Actor**: Field Worker (Maria Santos)  
**Goal**: Upload and process bird photos from morning survey  
**Precondition**: Maria has 25 photos on her tablet from Site A survey  

**Normal Flow**:
1. Maria logs in and navigates to Image Processing Dashboard
2. Clicks "Upload Images" button
3. Drags all 25 photos into drop zone
4. Enters title: "Site A - Morning Survey - Oct 14"
5. Adds site hint: "Site A" (auto-completed from recent sites)
6. Clicks "Upload All" button
7. System uploads all 25 images (status: CAPTURED)
8. Success notification: "25 images uploaded successfully"
9. Maria clicks "Process Images" from dashboard
10. Reviews grid of 25 thumbnails
11. Clicks "Clarify with AI" on first 20 clear images
12. Clicks "Process Later" on 5 blurry images
13. Watches progress bar as each image processes
14. After 3 minutes, all 20 images processed (status: ORGANIZED)
15. Dashboard shows: "20 images ready for review"

**Alternative Flow 1A**: Upload fails for 3 images (too large)
- System shows error: "3 files exceed 10MB limit"
- Displays red badges on failed files
- Maria clicks "Continue with 22 images"
- Successfully uploads remaining images

**Alternative Flow 3A**: AI processing takes longer than expected
- After 30 seconds, system shows estimated time: "~5 min remaining"
- Maria clicks "Process in Background"
- Receives email notification when complete

**Post-condition**: 20 images ready for review, 5 images saved for later processing

**Frequency**: Daily (average 2-3 survey uploads per day)

---

### **Use Case 2: Quality Control Review**

**Actor**: Data Analyst (Dr. Alex Kim)  
**Goal**: Review 100 AI-processed images for accuracy  
**Precondition**: 100 images in ORGANIZED status awaiting review  

**Normal Flow**:
1. Dr. Kim navigates to Review Results page
2. Sees first result with Little Egret detection (85% confidence)
3. Reviews bounding box on image - correct detection
4. Presses 'A' key to approve (keyboard shortcut)
5. Toast notification: "Approved - Advancing to next"
6. Second result shows Chinese Egret (92% confidence)
7. Visually confirms - correct species
8. Clicks green "Approve" button
9. Third result shows Intermediate Egret (45% confidence)
10. Dr. Kim unsure - clicks "Review Later"
11. Fourth result shows Western Cattle Egret (78% confidence)
12. Bounding box incorrect - wrong bird highlighted
13. Clicks red "Reject" button
14. Continues reviewing - completes 95 in 45 minutes
15. Session summary: "95 reviewed (70 approved, 20 rejected, 5 deferred)"

**Alternative Flow 2A**: AI detection completely wrong
- Result shows Little Egret but image clearly shows Great Egret
- Dr. Kim clicks "Override" button
- Modal opens with 6 egret species options
- Selects "Great Egret" with reason: "Larger size, yellow bill"
- Saves override - marked as OVERRIDDEN status
- Audit log records: User, timestamp, old/new species

**Alternative Flow 2B**: Multiple birds in one image
- Result shows "3 detections total"
- Dr. Kim toggles between bbox view and original
- Verifies all 3 birds correctly detected
- Approves result for all detections

**Alternative Flow 2C**: Batch approval for similar images
- 15 consecutive results all show Little Egret with >85% confidence
- Dr. Kim selects checkboxes on all 15 results
- Clicks "Approve Selected"
- Confirmation: "Approve 15 results?"
- Clicks "Confirm" - all 15 approved instantly

**Post-condition**: 70 approved results ready for allocation, 20 rejected (won't allocate), 5 deferred for expert review

**Frequency**: Daily (dedicated 1-hour review sessions)

---

### **Use Case 3: Census Allocation**

**Actor**: Site Manager (Carlos Rivera)  
**Goal**: Allocate 50 approved detections to census sites  
**Precondition**: 50 approved results pending allocation  

**Normal Flow**:
1. Carlos navigates to Allocate Results page
2. Sees first result: Chinese Egret at Site A (from site hint)
3. Site dropdown pre-selected to "Site A" based on hint
4. Date picker shows today's date
5. Carlos confirms allocation details correct
6. Clicks "Allocate to Census" button
7. Success: Result marked as ENGAGED status
8. Second result: Little Egret with no site hint
9. Carlos searches site dropdown for "Coastal Wetland B"
10. Selects site, confirms date
11. Allocates to census
12. Processes next 10 results - all from same site
13. Carlos uses "Apply to All" checkbox
14. Bulk allocates 10 results to Site C
15. Completes 50 allocations in 20 minutes

**Alternative Flow 3A**: Uncertain about correct site
- Result shows bird photo without clear location marker
- Carlos clicks "Skip Allocation"
- Result stays approved but unallocated
- Carlos adds note: "Verify location with field team"

**Alternative Flow 3B**: Site doesn't exist yet
- Need to allocate to new survey site
- Carlos clicks "Create New Site" link
- Opens site creation modal
- Enters site details, saves
- New site immediately available in dropdown
- Completes allocation

**Post-condition**: 50 detections allocated to census data, ready for analytics

**Frequency**: 2-3 times per week (batch allocation sessions)

---

### **Use Case 4: Error Recovery**

**Actor**: Field Worker (Maria Santos)  
**Goal**: Recover from failed upload and resume workflow  
**Precondition**: Network interruption during batch upload  

**Normal Flow**:
1. Maria uploads 30 images
2. At image 15, network connection drops
3. System detects connection loss
4. Shows error: "Network interrupted - 15 of 30 uploaded"
5. "Retry Failed" button appears
6. Maria checks network, reconnects
7. Clicks "Retry Failed"
8. System resumes upload from image 16
9. Successfully uploads remaining 15 images
10. Total: 30 images uploaded

**Alternative Flow 4A**: Browser crash during processing
- Maria processing 10 images
- Browser crashes at image 6
- Maria reopens browser, logs back in
- Dashboard shows: "6 images processing" with progress bar
- Background processing continues
- Completed images appear in review queue

**Post-condition**: All data preserved, workflow resumed seamlessly

**Frequency**: Rare but critical for data integrity

---

## 🎨 UX/UI Design Requirements

### **Visual Design**

#### Color Scheme (Government Standards)
```css
Primary Colors:
- Navy Blue (#1f2937): Headers, primary actions
- Gray (#6b7280): Secondary text, borders
- White (#ffffff): Background, cards

Status Colors:
- Success Green (#10b981): Approved, completed
- Warning Yellow (#f59e0b): Pending, medium confidence
- Danger Red (#ef4444): Rejected, errors
- Info Blue (#3b82f6): Captured, processing

Confidence Score Colors:
- High (>80%): #10b981 (Green)
- Medium (60-80%): #f59e0b (Yellow)  
- Low (<60%): #ef4444 (Red)
```

#### Typography
```css
Headings: 
- H1: 2.25rem, Bold, Navy
- H2: 1.875rem, Semi-Bold, Navy
- H3: 1.5rem, Semi-Bold, Gray-800

Body:
- Base: 1rem, Regular, Gray-700
- Small: 0.875rem, Regular, Gray-600
- Label: 0.875rem, Semi-Bold, Gray-700
```

#### Spacing & Layout
```css
Container: Max-width 1280px, centered
Card Padding: 1.5rem
Grid Gap: 1.5rem (24px)
Button Height: 2.5rem (40px)
Input Height: 2.5rem (40px)
Border Radius: 0.375rem (6px)
```

### **Component Library**

#### Image Card (Process/Review)
```html
<div class="image-card">
  <div class="image-preview">
    <img src="..." alt="..." />
    <span class="status-badge">CAPTURED</span>
  </div>
  <div class="card-body">
    <h6 class="card-title">Image Title</h6>
    <p class="meta">2.5 MB • 5 min ago</p>
    <div class="actions">
      <button class="btn-primary">Clarify with AI</button>
      <button class="btn-secondary">Process Later</button>
    </div>
  </div>
</div>
```

#### Progress Bar (Processing)
```html
<div class="progress-container">
  <div class="progress-bar" style="width: 60%">
    <span class="progress-text">60%</span>
  </div>
  <p class="progress-message">Detecting birds...</p>
</div>
```

#### Review Result Card
```html
<div class="review-card">
  <div class="image-container">
    <img src="bbox-image" id="review-image" />
    <div class="toggle-buttons">
      <button class="active">Box</button>
      <button>Original</button>
    </div>
  </div>
  <div class="detection-info">
    <h5>Chinese Egret</h5>
    <span class="confidence high">92%</span>
    <p class="meta">3 detections total</p>
  </div>
  <div class="action-buttons">
    <button class="btn-approve">Approve</button>
    <button class="btn-reject">Reject</button>
    <button class="btn-override">Override</button>
    <button class="btn-skip">Review Later</button>
  </div>
</div>
```

### **Interaction Patterns**

#### Hover States
- Image cards: Subtle shadow lift (0 → 4px)
- Buttons: Background darkens 10%
- Thumbnails: Border highlight (#3b82f6)

#### Loading States
- Buttons: Spinner icon, disabled state
- Progress bars: Animated striped pattern
- Skeleton screens: Gray pulse animation

#### Empty States
```html
<div class="empty-state">
  <i class="icon-large">📷</i>
  <h3>No images to process</h3>
  <p>Upload some images to get started!</p>
  <button>Upload Images</button>
</div>
```

#### Error States
```html
<div class="error-state">
  <i class="icon-large">⚠️</i>
  <h3>Processing Failed</h3>
  <p class="error-message">Network connection lost</p>
  <div class="actions">
    <button>Retry</button>
    <button>Cancel</button>
  </div>
</div>
```

### **Keyboard Navigation**

| Action | Key | Scope |
|--------|-----|-------|
| Approve | A | Review page |
| Reject | R | Review page |
| Override | O | Review page |
| Skip/Later | S | Review/Process page |
| Next Item | → | All list pages |
| Previous Item | ← | All list pages |
| Toggle View | T | Review page (bbox/original) |
| Select Item | Space | All list pages |

### **Mobile Responsiveness**

#### Breakpoints
```css
Desktop: ≥1024px (default)
Tablet: 768px - 1023px
Mobile: <768px
```

#### Mobile Adaptations
- Grid: 4 columns → 2 columns → 1 column
- Buttons: Stack vertically on mobile
- Images: Full-width on mobile
- Sidebars: Collapse by default
- Touch targets: Min 44x44px

---

## 📊 Success Metrics & KPIs

### **User Efficiency**
| Metric | Target | Measurement |
|--------|--------|-------------|
| Upload time (10 images) | <30 seconds | Time from click to confirmation |
| Processing time (1 image) | <10 seconds | AI inference + DB save |
| Review time (1 result) | <15 seconds | Average time per approval/rejection |
| Allocation time (1 result) | <20 seconds | Site selection + save |

### **User Satisfaction**
| Metric | Target | Measurement |
|--------|--------|-------------|
| Task completion rate | >95% | % of started workflows completed |
| Error rate | <2% | Failed actions / total actions |
| Training time | <1 hour | Time to productive use for new users |
| User satisfaction | >4.5/5 | Post-session survey rating |

### **System Performance**
| Metric | Target | Measurement |
|--------|--------|-------------|
| Page load time | <2 seconds | 95th percentile |
| AI processing accuracy | >85% | Correct detections / total |
| Uptime | 99.9% | Monthly availability |
| Concurrent users | 50+ | Simultaneous active sessions |

### **Data Quality**
| Metric | Target | Measurement |
|--------|--------|-------------|
| Review rate | >90% | Reviewed results / total processed |
| Override rate | <15% | Overridden results / total approved |
| Rejection rate | <20% | Rejected results / total processed |
| Allocation rate | >95% | Allocated results / approved results |

---

## 🔧 Implementation Checklist

### **Phase 1: Core Workflow** ✅
- [x] Upload images interface
- [x] AI processing integration
- [x] Review results page
- [x] Allocation interface
- [x] Status tracking (CAPTURED → ENGAGED)

### **Phase 2: UX Enhancements** 🔄
- [x] "Process Later" button
- [x] Bounding box visualization
- [x] Toggle original/bbox views
- [ ] Keyboard shortcuts
- [ ] Batch selection/actions
- [ ] Progress indicators
- [ ] Empty/error states

### **Phase 3: Advanced Features** 📋
- [ ] Drag-and-drop upload
- [ ] Background processing
- [ ] Undo actions
- [ ] Session summary
- [ ] Bulk allocation
- [ ] Export results
- [ ] Mobile optimization

### **Phase 4: Accessibility & Polish** 📋
- [ ] WCAG 2.1 AA compliance
- [ ] Screen reader support
- [ ] Keyboard-only navigation
- [ ] Color contrast audit
- [ ] Performance optimization
- [ ] Cross-browser testing
- [ ] User testing sessions

---

## 📝 Development Notes

### **Current Status (AGENTS.md §Development Efficiency)**
✅ GTD workflow implemented  
✅ AI model integration complete  
✅ Database models defined  
✅ Basic templates created  
✅ URL routing configured  
🔄 UX enhancements in progress  

### **Technical Debt**
- Add batch processing for multiple images
- Implement background task queue
- Add comprehensive error handling
- Optimize image loading performance
- Add caching for processed results

### **Future Enhancements**
- Offline mode with service workers
- Real-time collaboration (multi-user review)
- AI model selection per image
- Confidence threshold customization
- Advanced filtering and search
- Export to external systems

---

**🎯 Goal**: Create an intuitive, efficient image processing workflow that minimizes manual effort while maintaining data quality through human-in-the-loop validation.

**Reference**: See SAVE_FOR_LATER_WORKFLOW.md for workflow flexibility, AGENTS.md for technical implementation guidelines.





