"""
Management command to fix AI dimensions for existing processed images.

This command updates the stored ai_dimensions in the bounding_box field
for all existing ImageProcessingResult objects to match the actual image dimensions.
"""

from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.conf import settings
import logging
from PIL import Image
import io

from apps.image_processing.models import ImageProcessingResult

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Fix AI dimensions for existing processed images'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making changes',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update even if dimensions seem correct',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        self.stdout.write(
            self.style.SUCCESS('Starting AI dimensions fix...')
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )
        
        # Get all processing results
        processing_results = ImageProcessingResult.objects.all()
        total_count = processing_results.count()
        
        if total_count == 0:
            self.stdout.write(
                self.style.WARNING('No processing results found')
            )
            return
        
        self.stdout.write(f'Found {total_count} processing results to check')
        
        fixed_count = 0
        error_count = 0
        
        for i, result in enumerate(processing_results, 1):
            try:
                self.stdout.write(f'Processing {i}/{total_count}: {result.id}')
                
                # Check if this result has bounding box data
                if not result.bounding_box or 'ai_dimensions' not in result.bounding_box:
                    self.stdout.write(f'  No bounding box or ai_dimensions found, skipping')
                    continue
                
                # Get the image file
                image_upload = result.image_upload
                if not image_upload.image_file:
                    self.stdout.write(f'  No image file found, skipping')
                    continue
                
                # Get actual image dimensions
                try:
                    with image_upload.image_file.open('rb') as f:
                        image_content = f.read()
                    
                    image = Image.open(io.BytesIO(image_content))
                    actual_dimensions = image.size
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'  Error reading image: {e}')
                    )
                    error_count += 1
                    continue
                
                # Get stored AI dimensions
                stored_dimensions = result.bounding_box.get('ai_dimensions')
                
                self.stdout.write(f'  Stored AI dimensions: {stored_dimensions}')
                self.stdout.write(f'  Actual image dimensions: {actual_dimensions}')
                
                # Check if dimensions need fixing
                needs_fixing = (
                    stored_dimensions != actual_dimensions or 
                    force
                )
                
                if needs_fixing:
                    if dry_run:
                        self.stdout.write(
                            self.style.WARNING(f'  Would fix: {stored_dimensions} -> {actual_dimensions}')
                        )
                    else:
                        # Update the bounding box data
                        updated_bounding_box = result.bounding_box.copy()
                        updated_bounding_box['ai_dimensions'] = actual_dimensions
                        
                        # Update the result
                        result.bounding_box = updated_bounding_box
                        result.save(update_fields=['bounding_box'])
                        
                        self.stdout.write(
                            self.style.SUCCESS(f'  Fixed: {stored_dimensions} -> {actual_dimensions}')
                        )
                        fixed_count += 1
                else:
                    self.stdout.write(f'  Dimensions already correct')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  Error processing result {result.id}: {e}')
                )
                error_count += 1
        
        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write('FIX SUMMARY')
        self.stdout.write('='*50)
        self.stdout.write(f'Total results processed: {total_count}')
        self.stdout.write(f'Results fixed: {fixed_count}')
        self.stdout.write(f'Errors encountered: {error_count}')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('\nDRY RUN COMPLETED - No changes were made')
            )
            self.stdout.write(
                self.style.SUCCESS('Run without --dry-run to apply the fixes')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'\nSuccessfully fixed {fixed_count} processing results!')
            )
            if fixed_count > 0:
                self.stdout.write(
                    self.style.SUCCESS('All existing images should now display correct bounding boxes!')
                )
