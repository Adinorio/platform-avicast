import os
import hashlib
import io
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)

from .models import ImageUpload, ImageProcessingResult, ProcessingBatch
from .forms import ImageUploadForm, ImageProcessingForm
from .local_storage import LocalStorageManager
from .image_optimizer import ImageOptimizer
from .bird_detection_service import get_bird_detection_service
from .config import IMAGE_CONFIG
from .utils import generate_unique_filename, create_auto_title, calculate_file_hash

# Lazy storage manager initialization
def get_storage_manager():
    """Get storage manager instance when needed"""
    return LocalStorageManager()

@login_required
def image_upload_view(request):
    """Handle image upload - separate from processing"""
    if request.method == 'POST':
        if settings.DEBUG:
            logger.info(f"POST request received with FILES: {request.FILES}")
            logger.info(f"POST data: {request.POST}")
            logger.info(f"User: {request.user}, Authenticated: {request.user.is_authenticated}")

        form = ImageUploadForm(request.POST, request.FILES)
        if settings.DEBUG:
            logger.info(f"Form created, is_valid: {form.is_valid()}")
        if not form.is_valid():
            if settings.DEBUG:
                logger.warning(f"FORM VALIDATION FAILED - Form errors: {form.errors}")
                logger.warning(f"POST data: {request.POST}")
                logger.warning(f"FILES data: {list(request.FILES.keys())}")

        if form.is_valid():
            try:
                # Get uploaded files (now supports multiple)
                image_files = request.FILES.getlist('image_file')
                logger.info(f"Uploading {len(image_files)} image(s)")

                if not image_files:
                    messages.error(request, "No images selected for upload.")
                    return redirect('image_processing:upload')

                # Handle single file case (backward compatibility)
                if len(image_files) == 1:
                    image_files = [image_files[0]]

                uploaded_images = []

                for i, image_file in enumerate(image_files, 1):
                    if settings.DEBUG:
                        logger.info(f"Processing upload {i}/{len(image_files)}: {image_file.name}, size: {image_file.size}, type: {image_file.content_type}")

                    # Calculate file hash for deduplication
                    file_content = image_file.read()
                    file_hash = calculate_file_hash(file_content)
                    if settings.DEBUG:
                        logger.info(f"File hash calculated: {file_hash[:10]}...")

                    # Check for duplicates - allow re-uploads with different metadata
                    if settings.DEBUG:
                        logger.info(f"Checking for duplicates for file: {image_file.name}")
                    try:
                        existing_images = ImageUpload.objects.filter(file_hash=file_hash)
                        if settings.DEBUG:
                            logger.info(f"Query result: {existing_images.count()} existing images with same hash")
                        if existing_images.exists():
                            if settings.DEBUG:
                                logger.info(f"Found {existing_images.count()} existing image(s) with same hash")

                            # Check if this is a true duplicate (same user, same title, recent upload)
                            recent_duplicate = existing_images.filter(
                                uploaded_by=request.user,
                                title__icontains=form.cleaned_data.get('title', ''),
                                uploaded_at__gte=timezone.now() - timezone.timedelta(hours=IMAGE_CONFIG['DUPLICATE_CHECK_HOURS'])
                            ).first()

                            if recent_duplicate:
                                logger.info(f"Recent duplicate detected: {recent_duplicate.pk}")
                                logger.info(f"Duplicate details - Title: '{recent_duplicate.title}', User: {recent_duplicate.uploaded_by}, Time: {recent_duplicate.uploaded_at}")

                                # Add detailed warning message
                                messages.warning(request, f"""
                                <strong>Duplicate Image Detected!</strong><br>
                                You uploaded this exact image '{image_file.name}' recently with the title '{recent_duplicate.title}'.
                                <br><br>
                                <strong>Options:</strong>
                                <ul>
                                    <li>View the existing image: <a href="{reverse('image_processing:detail', args=[recent_duplicate.pk])}" class="alert-link">Click here</a></li>
                                    <li>Upload with a different title to create a new entry</li>
                                    <li>Skip this file and continue with others</li>
                                </ul>
                                """.strip())

                                # Instead of redirecting, continue to show the upload form with the warning
                                # Remove this file from processing and continue with others
                                continue
                            else:
                                logger.info(f"Allowing re-upload of same image with different metadata")
                                # Generate unique filename to avoid conflicts
                                unique_filename = generate_unique_filename(image_file.name)
                                logger.info(f"Generated unique filename: {unique_filename}")

                                messages.info(request, f"Image '{image_file.name}' was previously uploaded, but you can upload it again with different title/description.")

                                # Update the filename to avoid conflicts
                                image_file.name = unique_filename

                        logger.info(f"Proceeding with upload...")
                    except Exception as e:
                        logger.error(f"Error checking duplicates: {str(e)}")
                        # Continue with upload if duplicate check fails
                        logger.warning(f"Continuing with upload despite duplicate check error...")

                    # Reset file pointer for saving
                    logger.info(f"Resetting file pointer...")
                    image_file.seek(0)

                    # Create image upload record - ONLY UPLOAD, NO PROCESSING
                    logger.info(f"Creating ImageUpload object for {image_file.name}...")
                    image_upload = ImageUpload()
                    image_upload.uploaded_by = request.user
                    image_upload.file_size = image_file.size
                    image_upload.file_type = image_file.content_type
                    image_upload.file_hash = file_hash
                    image_upload.original_filename = image_file.name
                    image_upload.upload_status = ImageUpload.UploadStatus.UPLOADED  # Just uploaded, not processed

                    # Use form data for title/description if provided
                    if form.cleaned_data.get('title'):
                        image_upload.title = form.cleaned_data.get('title')
                    else:
                        # Auto-generate title from filename
                        image_upload.title = create_auto_title(image_file.name)

                    if form.cleaned_data.get('description'):
                        image_upload.description = form.cleaned_data.get('description')

                    # Save original file
                    logger.info(f"Saving original file...")
                    image_upload.image_file.save(image_file.name, image_file, save=False)
                    image_upload.save()
                    logger.info(f"Original file saved: {image_upload.image_file.path if hasattr(image_upload.image_file, 'path') else 'No path'}")

                    # Add to uploaded images list
                    uploaded_images.append(image_upload)

                # Handle post-upload routing and feedback
                if uploaded_images:
                    # Store upload results in session for modal display
                    request.session['upload_results'] = {
                        'total': len(uploaded_images),
                        'uploaded_ids': [str(img.pk) for img in uploaded_images]
                    }

                    # Success message and redirect
                    if len(uploaded_images) == 1:
                        messages.success(request, f"Image '{uploaded_images[0].title}' uploaded successfully! Ready for processing.")
                    else:
                        messages.success(request, f"{len(uploaded_images)} images uploaded successfully! Ready for processing.")

                    # Redirect to list with status filter to show uploaded images
                    logger.info(f"EXECUTING FINAL REDIRECT: Redirecting to list page with {len(uploaded_images)} uploaded images")
                    logger.info(f"Session data being set: {request.session.get('upload_results', 'NOT SET')}")
                    return redirect('image_processing:list')  # Go to list to see uploaded images
                else:
                    messages.error(request, "No images were uploaded successfully.")
                    return redirect('image_processing:upload')

            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                logger.error(f"UNCAUGHT UPLOAD ERROR: {str(e)}")
                logger.error(f"Error type: {type(e).__name__}")
                logger.error(f"Traceback: {error_details}")
                messages.error(request, f"Upload failed: {str(e)}")
                logger.warning("REDIRECTING TO UPLOAD PAGE DUE TO ERROR")
                return redirect('image_processing:upload')
    else:
        form = ImageUploadForm()

    return render(request, 'image_processing/upload.html', {'form': form})

def process_image_with_storage(image_upload, file_content):
    """Process image with local storage optimization and real bird detection"""
    import time
    import threading
    
    def update_progress(step, progress, description=""):
        """Update progress with real-time feedback"""
        try:
            image_upload.processing_step = step
            image_upload.processing_progress = progress
            image_upload.save(update_fields=['processing_step', 'processing_progress'])
            logger.info(f"Progress Update: {step} - {progress}% - {description}")
        except Exception as e:
            logger.error(f"Error updating progress: {str(e)}")
    
    def gradual_progress(start_progress, end_progress, step_name, duration=2.0, description_prefix=""):
        """Simulate gradual progress over time"""
        steps = end_progress - start_progress
        if steps <= 0:
            return
        
        # Update progress immediately for real-time feedback
        for i in range(steps + 1):
            current_progress = start_progress + i
            current_description = f"{description_prefix}... {current_progress}%"
            update_progress(step_name, current_progress, current_description)
            # Small delay to allow frontend to catch up
            time.sleep(IMAGE_CONFIG['PROGRESS_UPDATE_DELAY'])
    
    try:
        start_time = time.time()
        logger.info(f"Starting processing for image {image_upload.pk}")
        
        # Step 1: Start processing (0-20%)
        logger.info("Step 1: Starting processing...")
        update_progress(ImageUpload.ProcessingStep.READING_FILE, 0, "Initializing...")
        
        image_upload.start_processing()
        logger.info("start_processing completed")
        
        # Gradual progress for initialization and file reading
        gradual_progress(0, 20, ImageUpload.ProcessingStep.READING_FILE, 1.5, "Reading image file")

        # Step 2: Dual optimization - storage and AI versions (20-50%)
        logger.info("Step 2: Creating dual optimizations...")
        update_progress(ImageUpload.ProcessingStep.OPTIMIZING, 20, "Creating storage and AI versions...")
        
        optimizer = ImageOptimizer()
        logger.info("Optimizing image for both storage and AI processing...")

        # Create AI-optimized version for YOLO - NOTE: This is NOT used for detection!
        # The AI model processes the original file_content, not this optimized version
        ai_dims = IMAGE_CONFIG['AI_DIMENSIONS']
        gradual_progress(20, 35, ImageUpload.ProcessingStep.OPTIMIZING, 1.0, f"Creating AI-optimized version ({ai_dims[0]}x{ai_dims[1]}) (not used for detection)")
        ai_content, original_size, ai_size, ai_dimensions = optimizer.optimize_for_ai(file_content)
        logger.info(f"AI optimization complete: {original_size} -> {ai_size} bytes, AI dimensions: {ai_dimensions}")
        logger.info(f"NOTE: AI model will process ORIGINAL image, not this 640x640 version")

        # Create storage-optimized version - for reference only
        storage_dims = IMAGE_CONFIG['STORAGE_DIMENSIONS']
        gradual_progress(35, 50, ImageUpload.ProcessingStep.OPTIMIZING, 1.0, f"Creating storage reference version (max {storage_dims[0]}x{storage_dims[1]})")
        storage_content, storage_size, format_used = optimizer.optimize_image(file_content)
        logger.info(f"Storage reference version created: {format_used}, {original_size} -> {storage_size} bytes (not saved)")

        # Step 3: Save ORIGINAL image (not optimized) to maintain coordinate system consistency (50-70%)
        logger.info("Step 3: Saving ORIGINAL image to maintain coordinate system...")
        update_progress(ImageUpload.ProcessingStep.SAVING, 50, "Saving original image...")
        
        from django.core.files.base import ContentFile
        # CRITICAL FIX: Save the ORIGINAL image, not the optimized version
        # This ensures the stored image dimensions match the AI processing dimensions
        original_file = ContentFile(file_content, image_upload.original_filename)
        image_upload.image_file.save(image_upload.original_filename, original_file, save=False)
        image_upload.compressed_size = len(file_content)  # Use original size
        image_upload.is_compressed = False  # Mark as not compressed since we're keeping original
        image_upload.save()
        logger.info("ORIGINAL image saved to maintain coordinate system consistency")
        
        # Gradual progress for saving
        gradual_progress(50, 70, ImageUpload.ProcessingStep.SAVING, 1.0, "Saving results")

        # Step 4: Run bird detection (70-95%)
        logger.info("Step 4: Running bird detection...")
        update_progress(ImageUpload.ProcessingStep.DETECTING, 70, "Initializing AI model...")
        
        try:
            from .bird_detection_service import get_bird_detection_service
            
            detection_service = get_bird_detection_service()
            if detection_service.is_available():
                logger.info("Bird detection service available, running detection...")
                
                # Gradual progress for AI model loading
                gradual_progress(70, 80, ImageUpload.ProcessingStep.DETECTING, 1.5, "Loading YOLO model")
                
                # Gradual progress for image analysis
                gradual_progress(80, 90, ImageUpload.ProcessingStep.DETECTING, 2.0, "Analyzing with AI (original image)")
                
                # Gradual progress for bird detection
                gradual_progress(90, 95, ImageUpload.ProcessingStep.DETECTING, 2.5, "Detecting birds")
                
                # CRITICAL: Use file_content (original image) for detection, NOT the 640x640 optimized version
                # This ensures coordinates are in the correct coordinate system
                # The original image will be saved to maintain coordinate system consistency
                detection_result = detection_service.detect_birds(file_content, image_upload.original_filename)

                # Get user-friendly summary for better feedback
                user_summary = detection_service.get_user_friendly_error_summary(detection_result)

                if detection_result['success']:
                    logger.info(f"Detection successful: {detection_result['total_detections']} birds found")

                    # Create processing result with real detection data
                    if not hasattr(image_upload, 'processing_result'):
                        from .models import ImageProcessingResult
                        import uuid

                        # Use the best detection result
                        best_detection = detection_result['best_detection']

                        if best_detection:
                            detected_species = best_detection['species']
                            confidence_score = best_detection['confidence']
                            bounding_box = best_detection['bounding_box']
                        else:
                            # No birds detected
                            detected_species = None
                            confidence_score = 0.0
                            bounding_box = {}

                        # Store all detections in the bounding_box field for visualization
                        all_detections = detection_result.get('detections', [])

                        # CRITICAL FIX: Use the actual dimensions that the AI model processed
                        # Since we're using file_content (original image), the AI processed the original dimensions
                        from PIL import Image
                        original_image = Image.open(io.BytesIO(file_content))
                        actual_ai_dimensions = original_image.size

                        detection_data = {
                            'best_detection': bounding_box,
                            'all_detections': [
                                {
                                    'species': det['species'],
                                    'confidence': det['confidence'],
                                    'bounding_box': det['bounding_box']
                                } for det in all_detections
                            ],
                            'total_count': len(all_detections),
                            'ai_dimensions': actual_ai_dimensions,  # Store ACTUAL AI processing dimensions
                            'user_feedback': user_summary  # Store user-friendly feedback
                        }
                        logger.info(f"CRITICAL FIX: Stored ACTUAL AI dimensions: {actual_ai_dimensions} (not the 640x640 optimization)")

                        processing_result = ImageProcessingResult.objects.create(
                            id=uuid.uuid4(),
                            image_upload=image_upload,
                            detected_species=detected_species,
                            confidence_score=confidence_score,
                            bounding_box=detection_data,  # Store comprehensive detection data including ai_dimensions
                            total_detections=detection_result['total_detections'],
                            processing_status=ImageProcessingResult.ProcessingStatus.COMPLETED,
                            ai_model='YOLO_V8',
                            model_version=detection_result['model_used'],
                            processing_device=detection_result['device_used'],
                            inference_time=detection_result.get('inference_time', 0.0),
                            model_confidence_threshold=detection_result['confidence_threshold'],
                            review_status=ImageProcessingResult.ReviewStatus.PENDING,  # Ready for review
                            review_notes='',
                            is_overridden=False
                        )
                        logger.info(f"Processing result created with real detection: {processing_result.pk}")
                        logger.info(f"Species: {detected_species}, Confidence: {confidence_score}")
                        logger.info(f"Total detections: {detection_result['total_detections']}")
                    else:
                        logger.info("Processing result already exists")
                else:
                    logger.error(f"Detection failed: {user_summary['message']}")
                    # Create a failed processing result with user-friendly error message
                    from PIL import Image
                    original_image = Image.open(io.BytesIO(file_content))
                    actual_ai_dimensions = original_image.size
                    error_message = f"{user_summary['title']}: {user_summary['message']}"
                    if user_summary['user_guidance']:
                        error_message += " | " + " | ".join(user_summary['user_guidance'][:2])  # Include first 2 suggestions
                    _create_failed_processing_result(image_upload, error_message, actual_ai_dimensions)
            else:
                logger.warning("Bird detection service not available, using fallback")
                _create_fallback_processing_result(image_upload)
                
        except Exception as e:
            logger.error(f"Error during bird detection: {str(e)}")
            # Create a failed processing result with correct dimensions
            from PIL import Image
            original_image = Image.open(io.BytesIO(file_content))
            actual_ai_dimensions = original_image.size
            _create_failed_processing_result(image_upload, str(e), actual_ai_dimensions)
        
        # Complete processing
        logger.info("Completing processing...")
        update_progress(ImageUpload.ProcessingStep.COMPLETE, 95, "Finalizing results...")
        
        # Final progress update
        gradual_progress(95, 100, ImageUpload.ProcessingStep.COMPLETE, 0.5, "Completing")
        
        image_upload.complete_processing()
        
        # Calculate and log actual processing time
        total_time = time.time() - start_time
        logger.info(f"Processing completed successfully in {total_time:.2f} seconds")
        
        # Store actual processing time in the model if available
        try:
            if hasattr(image_upload, 'processing_duration'):
                from datetime import timedelta
                image_upload.processing_duration = timedelta(seconds=total_time)
                image_upload.save(update_fields=['processing_duration'])
        except Exception as duration_error:
            logger.warning(f"Could not save processing duration: {str(duration_error)}")
            # Don't fail the entire processing for this minor issue
        
        # Check storage usage (archive functionality can be added later)
        # storage_manager = get_storage_manager()
        # storage_manager.check_and_archive_if_needed()
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Image processing error: {str(e)}")
        logger.error(f"Traceback: {error_details}")
        image_upload.mark_failed()
        # Don't re-raise the error - let the upload continue
        logger.error(f"Image processing failed for {image_upload.pk}, but upload will continue")

@login_required
def image_list_view(request):
    """Display list of uploaded images with storage information"""
    # Get user's images or all images if admin
    if request.user.is_staff:
        images = ImageUpload.objects.all()
    else:
        images = ImageUpload.objects.filter(uploaded_by=request.user)
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        images = images.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(original_filename__icontains=search_query)
        )
    
    # Filter by upload status
    status = request.GET.get('status', '')
    if status:
        images = images.filter(upload_status=status)

    # Filter by storage tier
    storage_tier = request.GET.get('storage_tier', '')
    if storage_tier:
        images = images.filter(storage_tier=storage_tier)
    
    # Filter by compression status
    compression_status = request.GET.get('compression_status', '')
    if compression_status == 'compressed':
        images = images.filter(is_compressed=True)
    elif compression_status == 'uncompressed':
        images = images.filter(is_compressed=False)
    
    # Pagination
    paginator = Paginator(images, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get storage statistics
    storage_manager = get_storage_manager()
    storage_stats = storage_manager.get_storage_usage()
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status': status,
        'storage_tier': storage_tier,
        'compression_status': compression_status,
        'storage_stats': storage_stats,
        'total_images': images.count(),
        'compressed_images': images.filter(is_compressed=True).count(),
        'uncompressed_images': images.filter(is_compressed=False).count(),
    }
    
    return render(request, 'image_processing/list.html', context)

@login_required
def image_detail_view(request, pk):
    """Display detailed view of an image with storage information"""
    image = get_object_or_404(ImageUpload, pk=pk)
    
    # Check if user can view this image
    if not request.user.is_staff and image.uploaded_by != request.user:
        messages.error(request, "You don't have permission to view this image.")
        return redirect('image_processing:list')
    
    # Get processing result if exists
    try:
        processing_result = image.processing_result
    except ImageProcessingResult.DoesNotExist:
        processing_result = None
    
    # Generate image with bounding boxes if processing result exists
    processed_image_url = None
    if processing_result and processing_result.bounding_box and image.image_file:
        try:
            from .visualization_utils import draw_detections_on_image

            # Read the original image
            with image.image_file.open('rb') as f:
                image_content = f.read()

            # Get the actual dimensions that the AI model processed
            # Since we're using file_content (original image), the AI processed the original dimensions
            from PIL import Image
            original_image = Image.open(io.BytesIO(image_content))
            ai_dimensions = original_image.size  # Use actual original image dimensions
            logger.info(f"AI processed original image dimensions: {ai_dimensions}")
            
            # CRITICAL FIX: Always use the actual image dimensions for visualization
            # The AI model always processes the original image, regardless of what's stored
            # This fixes the issue where old processed images had wrong ai_dimensions (640x640)
            # stored but the AI actually processed the original image dimensions
            if processing_result.bounding_box.get('ai_dimensions'):
                stored_ai_dims = processing_result.bounding_box['ai_dimensions']
                logger.info(f"Stored AI dimensions: {stored_ai_dims}, Actual image dimensions: {ai_dimensions}")
                
                if stored_ai_dims != ai_dimensions:
                    logger.warning(f"AI dimensions mismatch detected! Stored: {stored_ai_dims}, Actual: {ai_dimensions}")
                    logger.info(f"Using ACTUAL image dimensions for visualization (AI always processes original image)")
                    # Keep ai_dimensions as the actual image dimensions (correct)
                else:
                    logger.info(f"AI dimensions match - using actual image dimensions: {ai_dimensions}")
            else:
                logger.info(f"No stored AI dimensions found - using actual image dimensions: {ai_dimensions}")

            # Prepare detections for visualization
            detections = []
            if processing_result.bounding_box.get('all_detections'):
                logger.info(f"Processing {len(processing_result.bounding_box['all_detections'])} detections for visualization")
                for i, detection in enumerate(processing_result.bounding_box['all_detections'], 1):
                    bbox = detection.get('bounding_box', {})
                    logger.info(f"Detection {i}: species={detection.get('species')}, bbox={bbox}")
                    detections.append({
                        'species': detection.get('species', 'Bird'),
                        'confidence': detection.get('confidence', 0.0),
                        'bounding_box': bbox
                    })

            # Get the actual image dimensions for debugging
            display_width, display_height = original_image.size
            logger.info(f"Display image size: {display_width}x{display_height}")

            # Draw detections on image using actual AI dimensions
            # ai_dimensions now contains the ACTUAL image dimensions (not stored wrong dimensions)
            processed_image_bytes = draw_detections_on_image(
                image_content,
                detections,
                output_format='bytes',
                ai_processing_size=ai_dimensions  # Use actual AI processing dimensions for accurate scaling
            )

            # Save processed image temporarily
            from django.core.files.base import ContentFile
            from django.core.files.storage import default_storage
            import uuid
            import os

            # Ensure temp directory exists
            temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
            os.makedirs(temp_dir, exist_ok=True)

            # Create a temporary filename
            temp_filename = f"processed_{uuid.uuid4().hex[:8]}.jpg"
            temp_path = f"temp/{temp_filename}"

            # Save to temporary storage
            processed_image_url = default_storage.save(
                temp_path,
                ContentFile(processed_image_bytes)
            )

            # Store the temp file path in session for cleanup
            if not hasattr(request, 'session'):
                request.session = {}
            temp_files = request.session.get('temp_processed_images', [])
            temp_files.append(processed_image_url)
            # Keep only last 10 temp files
            if len(temp_files) > 10:
                temp_files = temp_files[-10:]
            request.session['temp_processed_images'] = temp_files

        except Exception as e:
            logger.error(f"Error generating processed image: {e}")
            processed_image_url = None
    
    # Get storage information
    storage_info = image.get_storage_info()
    
    context = {
        'image_upload': image,
        'processing_result': processing_result,
        'storage_info': storage_info,
        'processed_image_url': processed_image_url,
    }
    
    return render(request, 'image_processing/detail.html', context)

@login_required
def storage_status_view(request):
    """Display storage status and management options"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to view storage status.")
        return redirect('image_processing:list')
    
    # Get storage usage
    storage_manager = get_storage_manager()
    storage_usage = storage_manager.get_storage_usage()
    
    # Get storage recommendations
    recommendations = storage_manager._get_storage_recommendations()
    
    # Get recent uploads
    recent_uploads = ImageUpload.objects.order_by('-uploaded_at')[:10]
    
    context = {
        'storage_usage': storage_usage,
        'recommendations': recommendations,
        'recent_uploads': recent_uploads,
    }
    
    return render(request, 'image_processing/storage_status.html', context)

@login_required
def storage_cleanup_view(request):
    """Handle storage cleanup operations"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to perform storage cleanup.")
        return redirect('image_processing:list')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        days = int(request.POST.get('days', 30))
        
        try:
            if action == 'cleanup':
                # Perform actual cleanup
                storage_manager = get_storage_manager()
                result = storage_manager.cleanup_old_files(days)
                messages.success(request, f"Storage cleanup completed! Archived {result['archived_count']} files, freed {result['freed_space_mb']} MB")
            elif action == 'optimize':
                # Optimize uncompressed images
                optimize_uncompressed_images()
                messages.success(request, "Image optimization completed!")
            elif action == 'archive':
                # Archive old files
                storage_manager = get_storage_manager()
                result = storage_manager.archive_old_files(days)
                messages.success(request, f"Archived {result['archived_count']} files")
            
            return redirect('image_processing:storage_status')
            
        except Exception as e:
            messages.error(request, f"Operation failed: {str(e)}")
            return redirect('image_processing:storage_status')
    
    return render(request, 'image_processing/storage_cleanup.html')

def optimize_uncompressed_images():
    """Optimize all uncompressed images"""
    uncompressed_images = ImageUpload.objects.filter(is_compressed=False)
    
    for image in uncompressed_images:
        try:
            if image.image_file:
                # Read original file
                with image.image_file.open('rb') as f:
                    file_content = f.read()
                
                # Optimize
                optimizer = ImageOptimizer()
                optimized_content, new_size, format_used = optimizer.optimize_image(file_content)
                
                # Save optimized version
                from django.core.files.base import ContentFile
                optimized_file = ContentFile(optimized_content, f"optimized_{image.original_filename}")
                
                # Update database record
                image.image_file.save(f"optimized_{image.original_filename}", optimized_file, save=False)
                image.compressed_size = new_size
                image.is_compressed = True
                image.save()
                
        except Exception as e:
            logger.error(f"Failed to optimize image {image.id}: {e}")

@login_required
def image_delete_view(request, pk):
    """Delete an image (admin only)"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to delete images.")
        return redirect('image_processing:list')
    
    image = get_object_or_404(ImageUpload, pk=pk)
    
    if request.method == 'POST':
        try:
            # Delete the image file
            if image.image_file:
                if os.path.exists(image.image_file.path):
                    os.remove(image.image_file.path)
            
            # Delete the database record
            image.delete()
            
            messages.success(request, "Image deleted successfully!")
            return redirect('image_processing:list')
            
        except Exception as e:
            messages.error(request, f"Delete failed: {str(e)}")
    
    return render(request, 'image_processing/delete_confirm.html', {'image': image})

@login_required
def restore_archived_image(request, pk):
    """Restore an archived image to active storage"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to restore images.")
        return redirect('image_processing:list')
    
    image = get_object_or_404(ImageUpload, pk=pk)
    
    if image.storage_tier == 'ARCHIVE':
        try:
            storage_manager = get_storage_manager()
            success = storage_manager.restore_from_archive(str(image.pk))
            if success:
                messages.success(request, "Image restored successfully!")
            else:
                messages.error(request, "Failed to restore image.")
        except Exception as e:
            messages.error(request, f"Restore failed: {str(e)}")
    else:
        messages.warning(request, "This image is not archived.")
    
    return redirect('image_processing:detail', pk=pk)

# API endpoints for AJAX operations
@csrf_exempt
@require_http_methods(["POST"])
def api_upload_progress(request):
    """API endpoint for upload progress tracking"""
    # This would be implemented for real-time upload progress
    return JsonResponse({'status': 'success'})

@login_required
def api_storage_stats(request):
    """API endpoint for storage statistics"""
    storage_manager = get_storage_manager()
    stats = storage_manager.get_storage_usage()
    return JsonResponse(stats)

@login_required
def api_image_search(request):
    """API endpoint for image search"""
    query = request.GET.get('q', '')
    if query:
        images = ImageUpload.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(original_filename__icontains=query)
        )[:10]

        results = []
        for image in images:
            results.append({
                'id': str(image.pk),
                'title': image.title,
                'filename': image.original_filename,
                'uploaded_at': image.uploaded_at.strftime('%Y-%m-%d %H:%M'),
                'storage_tier': image.storage_tier,
                'is_compressed': image.is_compressed,
            })

        return JsonResponse({'results': results})

    return JsonResponse({'results': []})

@login_required
def api_get_progress(request):
    """API endpoint to get processing progress for images"""
    image_ids = request.GET.getlist('image_ids[]', [])

    if not image_ids:
        return JsonResponse({'error': 'No image IDs provided'})

    try:
        images = ImageUpload.objects.filter(pk__in=image_ids)

        progress_data = []
        for image in images:
            progress_data.append({
                'id': str(image.pk),
                'status': image.upload_status,
                'step': image.processing_step,
                'step_display': image.get_processing_step_display() if image.processing_step else '',
                'progress': image.processing_progress,
                'started_at': image.processing_started_at.isoformat() if image.processing_started_at else None,
                'completed_at': image.processing_completed_at.isoformat() if image.processing_completed_at else None,
                'duration': str(image.processing_duration) if image.processing_duration else None,
            })

        return JsonResponse({
            'success': True,
            'images': progress_data
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def api_progress(request, image_id):
    """API endpoint to get progress for a single image"""
    try:
        image = get_object_or_404(ImageUpload, pk=image_id)

        # Check if user can view this image
        if not request.user.is_staff and image.uploaded_by != request.user:
            return JsonResponse({'error': 'Permission denied'}, status=403)

        return JsonResponse({
            'id': str(image.pk),
            'status': image.upload_status,
            'step': image.processing_step,
            'step_display': image.get_processing_step_display() if image.processing_step else '',
            'progress': image.processing_progress,
            'started_at': image.processing_started_at.isoformat() if image.processing_started_at else None,
            'completed_at': image.processing_completed_at.isoformat() if image.processing_completed_at else None,
            'duration': str(image.processing_duration) if image.processing_duration else None,
        })

    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def api_batch_process(request):
    """API endpoint for batch processing of images"""
    try:
        import json
        data = json.loads(request.body)
        image_ids = data.get('image_ids', [])

        if not image_ids:
            return JsonResponse({'success': False, 'error': 'No image IDs provided'})

        # Get images that are in uploaded status OR failed status (for retry)
        images_to_process = ImageUpload.objects.filter(
            pk__in=image_ids,
            upload_status__in=[ImageUpload.UploadStatus.UPLOADED, ImageUpload.UploadStatus.FAILED]
        )

        if not images_to_process.exists():
            return JsonResponse({'success': False, 'error': 'No valid images found to process. Images must be in UPLOADED or FAILED status to be processed.'})

        processed_count = 0
        failed_count = 0

        for image in images_to_process:
            try:
                # Log if this is a retry of a failed image
                if image.upload_status == ImageUpload.UploadStatus.FAILED:
                    logger.info(f"Retrying failed image {image.pk}")
                else:
                    logger.info(f"Processing new image {image.pk}")
                
                # Read file content for processing
                with image.image_file.open('rb') as f:
                    file_content = f.read()

                # Process the image
                process_image_with_storage(image, file_content)
                processed_count += 1
                logger.info(f"Successfully processed image {image.pk}")

            except Exception as e:
                logger.error(f"Failed to process image {image.pk}: {str(e)}")
                image.mark_failed()
                failed_count += 1

        return JsonResponse({
            'success': True,
            'processed': processed_count,
            'failed': failed_count,
            'message': f'Processed {processed_count} images successfully, {failed_count} failed'
        })

    except Exception as e:
        logger.error(f"Batch processing error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Batch processing failed: {str(e)}'
        }, status=500)

@login_required
def review_view(request):
    """Display images ready for review"""
    if not request.user.is_staff:
        messages.error(request, "Access denied. Staff only.")
        return redirect('image_processing:list')

    # Get processing results ready for review (not just uploads)
    results_to_review = ImageProcessingResult.objects.filter(
        review_status=ImageProcessingResult.ReviewStatus.PENDING,
        processing_status=ImageProcessingResult.ProcessingStatus.COMPLETED
    ).select_related('image_upload', 'image_upload__uploaded_by').order_by('-created_at')

    # Get approved results
    approved_results = ImageProcessingResult.objects.filter(
        review_status=ImageProcessingResult.ReviewStatus.APPROVED,
        processing_status=ImageProcessingResult.ProcessingStatus.COMPLETED
    ).select_related('image_upload', 'image_upload__uploaded_by').order_by('-reviewed_at')

    # Get rejected results
    rejected_results = ImageProcessingResult.objects.filter(
        review_status=ImageProcessingResult.ReviewStatus.REJECTED,
        processing_status=ImageProcessingResult.ProcessingStatus.COMPLETED
    ).select_related('image_upload', 'image_upload__uploaded_by').order_by('-reviewed_at')

    # Get overridden results
    overridden_results = ImageProcessingResult.objects.filter(
        review_status=ImageProcessingResult.ReviewStatus.OVERRIDDEN,
        processing_status=ImageProcessingResult.ProcessingStatus.COMPLETED
    ).select_related('image_upload', 'image_upload__uploaded_by').order_by('-overridden_at')

    # Get counts for different statuses
    pending_count = results_to_review.count()
    approved_count = approved_results.count()
    rejected_count = rejected_results.count()
    overridden_count = overridden_results.count()

    context = {
        'results_to_review': results_to_review,
        'approved_results': approved_results,
        'rejected_results': rejected_results,
        'overridden_results': overridden_results,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'overridden_count': overridden_count,
    }
    return render(request, 'image_processing/review.html', context)

@login_required
def process_batch_view(request, pk):
    """Process a batch of images"""
    if not request.user.is_staff:
        messages.error(request, "Access denied. Staff only.")
        return redirect('image_processing:list')
    
    try:
        # Get the image to process
        image = get_object_or_404(ImageUpload, pk=pk)
        
        # Process the image
        if image.upload_status == ImageUpload.UploadStatus.UPLOADED:
            # Re-process the image
            try:
                with open(image.image_file.path, 'rb') as f:
                    file_content = f.read()
                process_image_with_storage(image, file_content)
                messages.success(request, f"Image '{image.title}' processed successfully!")
            except Exception as e:
                messages.error(request, f"Processing failed: {str(e)}")
        else:
            messages.info(request, f"Image '{image.title}' is already processed.")
        
        return redirect('image_processing:detail', pk=pk)
        
    except Exception as e:
        messages.error(request, f"Error processing image: {str(e)}")
        return redirect('image_processing:detail', pk=pk)

@login_required
def allocate_view(request):
    """Allocate approved results to census data"""
    if not request.user.is_staff:
        messages.error(request, "Access denied. Staff only.")
        return redirect('image_processing:list')
    
    # Get approved results that can be allocated
    approved_results = ImageProcessingResult.objects.filter(
        review_status__in=[
            ImageProcessingResult.ReviewStatus.APPROVED,
            ImageProcessingResult.ReviewStatus.OVERRIDDEN
        ]
    ).select_related('image_upload', 'image_upload__uploaded_by').order_by('-created_at')
    
    # Get sites for allocation (you'll need to implement this based on your sites system)
    # For now, we'll use mock data
    sites = [
        {'id': 1, 'name': 'Site A - Coastal Wetland', 'location': 'Eastern Coast'},
        {'id': 2, 'name': 'Site B - Inland Lake', 'location': 'Central Region'},
        {'id': 3, 'name': 'Site C - River Delta', 'location': 'Western Delta'},
    ]
    
    # Mock years and months for census data
    years = [2024, 2025, 2026]
    months = [
        {'id': 1, 'name': 'January', 'abbr': 'Jan'},
        {'id': 2, 'name': 'February', 'abbr': 'Feb'},
        {'id': 3, 'name': 'March', 'abbr': 'Mar'},
        {'id': 4, 'name': 'April', 'abbr': 'Apr'},
        {'id': 5, 'name': 'May', 'abbr': 'May'},
        {'id': 6, 'name': 'June', 'abbr': 'Jun'},
        {'id': 7, 'name': 'July', 'abbr': 'Jul'},
        {'id': 8, 'name': 'August', 'abbr': 'Aug'},
        {'id': 9, 'name': 'September', 'abbr': 'Sep'},
        {'id': 10, 'name': 'October', 'abbr': 'Oct'},
        {'id': 11, 'name': 'November', 'abbr': 'Nov'},
        {'id': 12, 'name': 'December', 'abbr': 'Dec'},
    ]
    
    context = {
        'approved_results': approved_results,
        'sites': sites,
        'years': years,
        'months': months,
    }
    return render(request, 'image_processing/allocate.html', context)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def clear_upload_results(request):
    """Clear upload results from session after modal is shown"""
    if 'upload_results' in request.session:
        del request.session['upload_results']
    return JsonResponse({'status': 'success'})

@login_required
@require_http_methods(["POST"])
def approve_result(request, result_id):
    """Approve a processing result"""
    if not request.user.is_staff:
        return JsonResponse({'status': 'error', 'message': 'Access denied'}, status=403)
    
    try:
        result = get_object_or_404(ImageProcessingResult, pk=result_id)
        notes = request.POST.get('notes', '')
        
        result.approve_result(request.user, notes)
        
        return JsonResponse({
            'status': 'success',
            'message': f'Result for "{result.image_upload.title}" approved successfully!'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error approving result: {str(e)}'
        }, status=500)

@login_required
@require_http_methods(["POST"])
def reject_result(request, result_id):
    """Reject a processing result"""
    if not request.user.is_staff:
        return JsonResponse({'status': 'error', 'message': 'Access denied'}, status=403)
    
    try:
        result = get_object_or_404(ImageProcessingResult, pk=result_id)
        notes = request.POST.get('notes', '')
        
        result.reject_result(request.user, notes)
        
        return JsonResponse({
            'status': 'success',
            'message': f'Result for "{result.image_upload.title}" rejected.'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error rejecting result: {str(e)}'
        }, status=500)

@login_required
@require_http_methods(["POST"])
def override_result(request, result_id):
    """Override a processing result with manual classification and/or count"""
    if not request.user.is_staff:
        return JsonResponse({'status': 'error', 'message': 'Access denied'}, status=403)
    
    try:
        result = get_object_or_404(ImageProcessingResult, pk=result_id)
        new_species = request.POST.get('species')
        new_count_str = request.POST.get('count')
        reason = request.POST.get('reason', '')
        
        # Validate that at least one field is being overridden
        if not new_species and not new_count_str:
            return JsonResponse({
                'status': 'error',
                'message': 'At least species or count must be provided for override'
            }, status=400)
        
        # Parse count if provided
        new_count = None
        if new_count_str:
            try:
                new_count = int(new_count_str)
                if new_count < 0:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Count must be a non-negative number'
                    }, status=400)
            except ValueError:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Count must be a valid number'
                }, status=400)

        # Use original species if not provided
        if not new_species:
            new_species = result.final_species

        result.override_result(request.user, new_species, reason, new_count)

        # Build success message
        changes = []
        if new_count is not None:
            changes.append(f'count: {new_count}')
        if new_species:
            changes.append(f'species: {new_species}')
        
        return JsonResponse({
            'status': 'success',
            'message': f'Result for "{result.image_upload.title}" overridden with {" and ".join(changes)}'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error overriding result: {str(e)}'
        }, status=500)

@login_required
def dashboard_view(request):
    """Display image processing dashboard with statistics and overview"""
    # Get user's images or all images if admin
    if request.user.is_staff:
        images = ImageUpload.objects.all()
    else:
        images = ImageUpload.objects.filter(uploaded_by=request.user)
    
    # Get statistics
    total_uploads = images.count()
    processed_uploads = images.filter(upload_status=ImageUpload.UploadStatus.PROCESSED).count()
    uploaded_images = images.filter(upload_status=ImageUpload.UploadStatus.UPLOADED).count()
    pending_review = ImageProcessingResult.objects.filter(review_status=ImageProcessingResult.ReviewStatus.PENDING).count()
    approved_results = ImageProcessingResult.objects.filter(review_status=ImageProcessingResult.ReviewStatus.APPROVED).count()
    
    # Get AI models available
    ai_models = [
        ('yolo_bird_detection', 'Bird Detection (YOLO)'),
        ('species_classification', 'Species Classification'),
        ('census_counting', 'Census Counting'),
    ]

    # Get AI model information from models directory
    import os
    models_dir = 'models'
    yolov5_models = []
    yolov8_models = []
    yolov9_models = []
    
    if os.path.exists(models_dir):
        for filename in os.listdir(models_dir):
            if filename.endswith('.pt'):
                file_path = os.path.join(models_dir, filename)
                file_size = os.path.getsize(file_path)
                size_mb = f"{file_size / (1024 * 1024):.1f}MB"
                
                model_info = {
                    'name': filename.replace('.pt', ''),
                    'size': size_mb,
                    'filename': filename,
                    'status': 'Ready'
                }
                
                if filename.startswith('yolov5'):
                    yolov5_models.append(model_info)
                elif filename.startswith('yolov8'):
                    yolov8_models.append(model_info)
                elif filename.startswith('yolov9'):
                    yolov9_models.append(model_info)
    
    # Sort models by name
    yolov5_models.sort(key=lambda x: x['name'])
    yolov8_models.sort(key=lambda x: x['name'])
    yolov9_models.sort(key=lambda x: x['name'])
    
    # Get recent uploads (all recent uploads)
    recent_uploads = images.filter(
        upload_status__in=[
            ImageUpload.UploadStatus.PROCESSED,
            ImageUpload.UploadStatus.UPLOADED,
            ImageUpload.UploadStatus.PROCESSING
        ]
    ).exclude(
        upload_status=ImageUpload.UploadStatus.UPLOADING  # Exclude stuck uploads
    ).order_by('-uploaded_at')[:5]
    
    # Get storage statistics
    storage_manager = get_storage_manager()
    storage_stats = storage_manager.get_storage_usage()
    
    context = {
        'total_uploads': total_uploads,
        'processed_uploads': processed_uploads,
        'uploaded_images': uploaded_images,
        'pending_review': pending_review,
        'approved_results': approved_results,
        'ai_models': ai_models,
        'yolov5_models': yolov5_models,
        'yolov8_models': yolov8_models,
        'yolov9_models': yolov9_models,
        'recent_uploads': recent_uploads,
        'storage_stats': storage_stats,
    }
    
    return render(request, 'image_processing/dashboard.html', context)

def _create_failed_processing_result(image_upload, error_message, ai_dimensions=(640, 640)):
    """Create a failed processing result"""
    try:
        from .models import ImageProcessingResult
        import uuid
        
        if not hasattr(image_upload, 'processing_result'):
            processing_result = ImageProcessingResult.objects.create(
                id=uuid.uuid4(),
                image_upload=image_upload,
                detected_species=None,
                confidence_score=0.0,
                bounding_box={
                    'best_detection': {},
                    'all_detections': [],
                    'total_count': 0,
                    'ai_dimensions': ai_dimensions  # Use actual AI dimensions for failed results
                },
                total_detections=0,
                processing_status=ImageProcessingResult.ProcessingStatus.FAILED,
                ai_model='YOLO_V8',
                model_version='unknown',
                processing_device='cpu',
                inference_time=0.0,
                model_confidence_threshold=0.25,
                review_status=ImageProcessingResult.ReviewStatus.PENDING,
                review_notes=f'Processing failed: {error_message}',
                is_overridden=False
            )
            logger.info(f"Failed processing result created: {processing_result.pk}")
    except Exception as e:
        logger.error(f"Error creating failed processing result: {str(e)}")

def _create_fallback_processing_result(image_upload):
    """Create a fallback processing result when detection service is unavailable"""
    try:
        from .models import ImageProcessingResult
        import uuid
        
        if not hasattr(image_upload, 'processing_result'):
            processing_result = ImageProcessingResult.objects.create(
                id=uuid.uuid4(),
                image_upload=image_upload,
                detected_species=None,
                confidence_score=0.0,
                bounding_box={
                    'best_detection': {},
                    'all_detections': [],
                    'total_count': 0,
                    'ai_dimensions': (640, 640)  # Default fallback dimensions
                },
                total_detections=0,
                processing_status=ImageProcessingResult.ProcessingStatus.COMPLETED,
                ai_model='YOLO_V8',
                model_version='fallback',
                processing_device='cpu',
                inference_time=0.0,
                model_confidence_threshold=0.25,
                review_status=ImageProcessingResult.ReviewStatus.PENDING,
                review_notes='Detection service unavailable - manual review required',
                is_overridden=False
            )
            logger.info(f"Fallback processing result created: {processing_result.pk}")
    except Exception as e:
        logger.error(f"Error creating fallback processing result: {str(e)}")

@login_required
def model_selection_view(request):
    """View for selecting and managing AI models"""
    # TEMPORARY WORKAROUND: Allow access for development/testing
    # TODO: Remove this and properly set up user permissions
    if not request.user.is_staff:
        messages.warning(request, "⚠️ DEVELOPMENT MODE: AI model management is temporarily open for testing. In production, only staff users should access this.")
        # For now, allow access but show warning
        # return redirect('image_processing:list')
    
    from .forms import ModelSelectionForm
    from .bird_detection_service import get_bird_detection_service
    
    detection_service = get_bird_detection_service()
    
    if request.method == 'POST':
        form = ModelSelectionForm(request.POST)
        if form.is_valid():
            ai_model = form.cleaned_data['ai_model']
            confidence_threshold = form.cleaned_data['confidence_threshold']
            
            # Switch to selected model
            if detection_service.switch_model(ai_model):
                messages.success(request, f"Successfully switched to {ai_model}")
            else:
                messages.error(request, f"Failed to switch to {ai_model}")
            
            # Update confidence threshold
            detection_service.confidence_threshold = confidence_threshold
            
            return redirect('image_processing:model_selection')
    else:
        # Pre-populate form with current settings
        initial_data = {
            'ai_model': detection_service.current_version,
            'confidence_threshold': detection_service.confidence_threshold
        }
        form = ModelSelectionForm(initial=initial_data)
    
    # Get model information
    model_info = detection_service.get_model_info()
    available_models = detection_service.get_available_models()
    
    context = {
        'form': form,
        'model_info': model_info,
        'available_models': available_models,
        'current_model': detection_service.current_version,
    }
    
    return render(request, 'image_processing/model_selection.html', context)

@login_required
def benchmark_models_view(request):
    """View for benchmarking different YOLO models"""
    # TEMPORARY WORKAROUND: Allow access for development/testing
    # TODO: Remove this and properly set up user permissions
    if not request.user.is_staff:
        messages.warning(request, "⚠️ DEVELOPMENT MODE: Model benchmarking is temporarily open for testing. In production, only staff users should access this.")
        # For now, allow access but show warning
        # return redirect('image_processing:list')
    
    from .bird_detection_service import get_bird_detection_service
    
    detection_service = get_bird_detection_service()
    
    if request.method == 'POST':
        # Get test image from request
        test_image = request.FILES.get('test_image')
        if test_image:
            try:
                # Read image content
                image_content = test_image.read()
                
                # Run benchmark
                benchmark_results = detection_service.benchmark_models(image_content)
                
                messages.success(request, "Benchmark completed successfully!")
                
                context = {
                    'benchmark_results': benchmark_results,
                    'test_image_name': test_image.name,
                    'test_image_size': len(image_content)
                }
                
                return render(request, 'image_processing/benchmark_results.html', context)
                
            except Exception as e:
                messages.error(request, f"Benchmark failed: {str(e)}")
        else:
            messages.error(request, "Please select a test image for benchmarking.")
    
    context = {
        'available_models': detection_service.get_available_models(),
        'total_models': len(detection_service.models)
    }
    
    return render(request, 'image_processing/benchmark_models.html', context)

@login_required
def debug_form_view(request):
    """Debug form view for testing evaluation run creation"""
    if not request.user.can_access_feature('image_processing'):
        messages.error(request, "You don't have permission to access image processing.")
        return redirect('home')

@login_required
def health_status_view(request):
    """Real-time health status monitoring for the detection service"""
    if not request.user.can_access_feature('image_processing'):
        messages.error(request, "You don't have permission to access health monitoring.")
        return redirect('home')

    from .bird_detection_service import get_bird_detection_service
    detection_service = get_bird_detection_service()

    # Get comprehensive health status
    health_status = detection_service.get_detection_health_status()
    model_info = detection_service.get_model_info()
    available_models = detection_service.get_available_models()

    # Add timestamp for monitoring
    import datetime
    health_status['timestamp'] = datetime.datetime.now().isoformat()

    context = {
        'health_status': health_status,
        'model_info': model_info,
        'available_models': available_models,
        'last_updated': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
    }

    return render(request, 'image_processing/health_status.html', context)
