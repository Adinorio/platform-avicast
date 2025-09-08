#!/usr/bin/env python
"""
Batch optimization command for processing all existing images in the repository.

Usage:
    python manage.py batch_optimize_images --help

Examples:
    # Optimize all unoptimized images
    python manage.py batch_optimize_images

    # Dry run to see what would be processed
    python manage.py batch_optimize_images --dry-run

    # Process only image_processing images
    python manage.py batch_optimize_images --app=image_processing

    # Process in smaller batches
    python manage.py batch_optimize_images --batch-size=10

    # Force re-optimization of completed images
    python manage.py batch_optimize_images --force
"""

import time
from typing import Dict, List, Optional, Tuple

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from apps.common.services.image_optimizer import UniversalImageOptimizer
from apps.fauna.models import Species
from apps.image_processing.models import ImageUpload
from apps.locations.models import Site


class Command(BaseCommand):
    help = "Batch optimize all existing images in the repository"

    def add_arguments(self, parser):
        parser.add_argument(
            '--app',
            type=str,
            choices=['image_processing', 'fauna', 'locations', 'all'],
            default='all',
            help='App to optimize images for (default: all)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without making changes',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Number of images to process in each batch (default: 50)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force re-optimization of already completed images',
        )
        parser.add_argument(
            '--max-images',
            type=int,
            help='Maximum number of images to process (for testing)',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(
                '🚀 Universal Image Batch Optimization Tool\n'
                '==============================================\n'
            )
        )

        # Get configuration
        app_filter = options['app']
        dry_run = options['dry_run']
        batch_size = options['batch_size']
        force = options['force']
        max_images = options['max_images']

        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No changes will be made\n'))

        # Get images to process
        images_to_process = self._get_images_to_process(app_filter, force, max_images)

        if not images_to_process:
            self.stdout.write(self.style.WARNING('No images found to process.'))
            return

        total_images = len(images_to_process)
        self.stdout.write(f'📊 Found {total_images} images to process\n')

        # Show breakdown by app
        self._show_app_breakdown(images_to_process)

        if dry_run:
            self.stdout.write(self.style.SUCCESS('✅ Dry run complete. Use --dry-run=False to process images.'))
            return

        # Confirm before processing
        if not self._confirm_processing(total_images):
            self.stdout.write(self.style.WARNING('❌ Operation cancelled by user.'))
            return

        # Process images
        self._process_images(images_to_process, batch_size)

    def _get_images_to_process(self, app_filter: str, force: bool, max_images: Optional[int]) -> List[Tuple]:
        """Get list of images that need optimization."""
        images_to_process = []

        # Build query filter
        base_filter = Q()
        if not force:
            base_filter = Q(optimization_status__in=['pending', 'failed', None])

        # Get images from each app
        apps_to_check = ['image_processing', 'fauna', 'locations'] if app_filter == 'all' else [app_filter]

        for app_name in apps_to_check:
            if app_name == 'image_processing':
                images = ImageUpload.objects.filter(base_filter).select_related()
                images_to_process.extend([('image_processing', img) for img in images])

            elif app_name == 'fauna':
                images = Species.objects.filter(base_filter).exclude(image='').select_related()
                images_to_process.extend([('fauna', img) for img in images])

            elif app_name == 'locations':
                # Site model doesn't have an image field, skip for now
                self.stdout.write(self.style.WARNING(f'⚠️  Skipping locations app - no image field found'))
                continue

        # Apply max_images limit
        if max_images and len(images_to_process) > max_images:
            images_to_process = images_to_process[:max_images]

        return images_to_process

    def _show_app_breakdown(self, images_to_process: List[Tuple]):
        """Show breakdown of images by app."""
        app_counts = {}
        for app_name, _ in images_to_process:
            app_counts[app_name] = app_counts.get(app_name, 0) + 1

        self.stdout.write('📂 Images by app:')
        for app_name, count in app_counts.items():
            self.stdout.write(f'   • {app_name}: {count} images')
        self.stdout.write('')

    def _confirm_processing(self, total_images: int) -> bool:
        """Ask for confirmation before processing."""
        self.stdout.write(
            self.style.WARNING(
                f'⚠️  About to process {total_images} images.\n'
                f'   This may take some time depending on image sizes.\n'
                f'   Continue? (y/N): '
            )
        )

        try:
            response = input().strip().lower()
            return response in ['y', 'yes']
        except (EOFError, KeyboardInterrupt):
            return False

    def _process_images(self, images_to_process: List[Tuple], batch_size: int):
        """Process images in batches."""
        total_images = len(images_to_process)
        processed_count = 0
        failed_count = 0
        total_space_saved = 0

        start_time = time.time()

        self.stdout.write(self.style.SUCCESS('▶️  Starting batch optimization...\n'))

        # Process in batches
        for i in range(0, total_images, batch_size):
            batch = images_to_process[i:i + batch_size]
            batch_number = (i // batch_size) + 1
            total_batches = (total_images + batch_size - 1) // batch_size

            self.stdout.write(f'📦 Processing batch {batch_number}/{total_batches} ({len(batch)} images)')

            batch_processed, batch_failed, batch_space_saved = self._process_batch(batch)
            processed_count += batch_processed
            failed_count += batch_failed
            total_space_saved += batch_space_saved

            # Show progress
            progress = (processed_count + failed_count) / total_images * 100
            self.stdout.write(f'   Progress: {progress:.1f}%')
        # Show final statistics
        self._show_final_stats(
            processed_count, failed_count, total_space_saved,
            total_images, start_time
        )

    def _process_batch(self, batch: List[Tuple]) -> Tuple[int, int, int]:
        """Process a single batch of images."""
        processed_count = 0
        failed_count = 0
        total_space_saved = 0

        optimizer = UniversalImageOptimizer()

        for app_name, image_obj in batch:
            try:
                # Read image content
                if hasattr(image_obj, 'image_file'):
                    # ImageUpload model
                    with image_obj.image_file.open('rb') as f:
                        image_content = f.read()
                elif hasattr(image_obj, 'image') and image_obj.image:
                    # Species model
                    with image_obj.image.open('rb') as f:
                        image_content = f.read()
                else:
                    # No image field or empty image
                    self.stdout.write(
                        self.style.ERROR(f'   ❌ {image_obj.__class__.__name__}: {image_obj.pk} (no image found)')
                    )
                    failed_count += 1
                    continue

                # Get original size
                original_size = len(image_content)

                # Optimize image
                optimized_result = optimizer.optimize_for_app(image_content, app_name)

                if optimized_result and optimized_result.get('optimized'):
                    # Save optimized versions
                    space_saved = self._save_optimized_versions(image_obj, optimized_result, original_size)
                    total_space_saved += space_saved

                    # Update optimization status
                    image_obj.optimization_status = 'completed'
                    image_obj.is_compressed = True
                    image_obj.save(update_fields=['optimization_status', 'is_compressed'])

                    processed_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'   ✅ {image_obj.__class__.__name__}: {image_obj.pk}')
                    )
                else:
                    failed_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'   ❌ {image_obj.__class__.__name__}: {image_obj.pk} (optimization failed)')
                    )

            except Exception as e:
                failed_count += 1
                self.stdout.write(
                    self.style.ERROR(f'   ❌ {image_obj.__class__.__name__}: {image_obj.pk} ({str(e)})')
                )

        return processed_count, failed_count, total_space_saved

    def _save_optimized_versions(self, image_obj, optimized_result: Dict, original_size: int) -> int:
        """Save optimized versions and return space saved."""
        from django.core.files.base import ContentFile

        space_saved = 0

        try:
            # Save optimized web version
            if optimized_result.get('optimized'):
                optimized_filename = f"batch_optimized_{image_obj.pk}.webp"
                image_obj.optimized_image.save(
                    optimized_filename,
                    ContentFile(optimized_result['optimized']),
                    save=False
                )
                optimized_size = len(optimized_result['optimized'])
                image_obj.optimized_size = optimized_size
                space_saved += original_size - optimized_size

            # Save thumbnail version
            if optimized_result.get('thumbnail'):
                thumbnail_filename = f"batch_thumb_{image_obj.pk}.jpg"
                image_obj.thumbnail.save(
                    thumbnail_filename,
                    ContentFile(optimized_result['thumbnail']),
                    save=False
                )
                image_obj.thumbnail_size = len(optimized_result['thumbnail'])

            # Save AI-processed version
            if optimized_result.get('ai_ready'):
                ai_filename = f"batch_ai_ready_{image_obj.pk}.jpg"
                image_obj.ai_processed_image.save(
                    ai_filename,
                    ContentFile(optimized_result['ai_ready']),
                    save=False
                )

        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'   ⚠️  Error saving optimized versions: {str(e)}')
            )

        return space_saved

    def _show_final_stats(self, processed: int, failed: int, space_saved: int,
                         total: int, start_time: float):
        """Show final processing statistics."""
        end_time = time.time()
        duration = end_time - start_time

        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS('🎉 BATCH OPTIMIZATION COMPLETE'))
        self.stdout.write('=' * 50)

        self.stdout.write(self.style.SUCCESS('📊 FINAL STATISTICS:'))
        self.stdout.write(f'   • Total images processed: {total}')
        self.stdout.write(f'   • Successfully optimized: {processed}')
        self.stdout.write(f'   • Failed: {failed}')
        self.stdout.write(f'   • Processing time: {duration:.1f} seconds')
        if space_saved > 0:
            self.stdout.write(f'   • Total space saved: {space_saved:,} bytes ({space_saved/1024/1024:.2f} MB)')

        self.stdout.write(self.style.SUCCESS('\n✅ Batch optimization completed successfully!'))

        if failed > 0:
            self.stdout.write(
                self.style.WARNING(f'⚠️  {failed} images failed to optimize. Check logs for details.')
            )
