import os
import hashlib
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.conf import settings

from .models import ImageUpload, ImageProcessingResult, ProcessingBatch
from .forms import ImageUploadForm, ImageProcessingForm
from .local_storage import LocalStorageManager
from .image_optimizer import ImageOptimizer

# Lazy storage manager initialization
def get_storage_manager():
    """Get storage manager instance when needed"""
    return LocalStorageManager()

@login_required
def image_upload_view(request):
    """Handle image upload with automatic processing"""
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Get uploaded file
                image_file = request.FILES['image_file']
                
                # Calculate file hash for deduplication
                file_content = image_file.read()
                file_hash = hashlib.sha256(file_content).hexdigest()
                
                # Check for duplicates
                existing_image = ImageUpload.objects.filter(file_hash=file_hash).first()
                if existing_image:
                    messages.warning(request, f"Duplicate image detected! This image was already uploaded by {existing_image.uploaded_by.get_full_name() or existing_image.uploaded_by.username}")
                    return redirect('image_processing:upload')
                
                # Reset file pointer for saving
                image_file.seek(0)
                
                # Create image upload record
                image_upload = form.save(commit=False)
                image_upload.uploaded_by = request.user
                image_upload.file_size = image_file.size
                image_upload.file_type = image_file.content_type
                image_upload.file_hash = file_hash
                image_upload.original_filename = image_file.name
                image_upload.upload_status = ImageUpload.UploadStatus.UPLOADED
                image_upload.save()
                
                # Process image with local storage
                process_image_with_storage(image_upload, file_content)
                
                messages.success(request, f"Image '{image_upload.title}' uploaded successfully!")
                return redirect('image_processing:detail', pk=image_upload.pk)
                
            except Exception as e:
                messages.error(request, f"Upload failed: {str(e)}")
                return redirect('image_processing:upload')
    else:
        form = ImageUploadForm()
    
    return render(request, 'image_processing/upload.html', {'form': form})

def process_image_with_storage(image_upload, file_content):
    """Process image with local storage optimization"""
    try:
        # Start processing
        image_upload.start_processing()
        
        # Optimize image
        optimizer = ImageOptimizer()
        optimized_content, new_size, format_used = optimizer.optimize_image(file_content)
        
        # Update image record with optimization info
        image_upload.compressed_size = new_size
        image_upload.is_compressed = True
        image_upload.upload_status = ImageUpload.UploadStatus.PROCESSED
        image_upload.save()
        
        # Save optimized image
        from django.core.files.base import ContentFile
        optimized_file = ContentFile(optimized_content, f"optimized_{image_upload.original_filename}")
        image_upload.image_file.save(f"optimized_{image_upload.original_filename}", optimized_file, save=False)
        image_upload.save()
        
        # Complete processing
        image_upload.complete_processing()
        
        # Check storage usage and archive if needed
        storage_manager = get_storage_manager()
        storage_manager.check_and_archive_if_needed()
        
    except Exception as e:
        image_upload.mark_failed()
        raise e

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
    
    # Get storage information
    storage_info = image.get_storage_info()
    
    context = {
        'image': image,
        'processing_result': processing_result,
        'storage_info': storage_info,
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
            print(f"Failed to optimize image {image.id}: {e}")

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
