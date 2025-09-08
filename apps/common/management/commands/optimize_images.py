"""
Django management command to optimize images across all apps
Usage: python manage.py optimize_images --app=all --dry-run
"""

from django.core.management.base import BaseCommand
from django.db.models import Q

from apps.common.services.image_optimizer import UniversalImageOptimizer


class Command(BaseCommand):
    help = "Optimize images across all apps in the repository"

    def add_arguments(self, parser):
        parser.add_argument(
            "--app",
            type=str,
            default="all",
            help="App to optimize images for (fauna, locations, image_processing, all)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be optimized without actually doing it",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force re-optimization of already optimized images",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=10,
            help="Number of images to process in each batch",
        )

    def handle(self, *args, **options):
        app_name = options["app"]
        dry_run = options["dry_run"]
        force = options["force"]
        batch_size = options["batch_size"]

        self.stdout.write(
            self.style.SUCCESS(f"🚀 Starting universal image optimization (dry_run={dry_run})")
        )

        optimizer = UniversalImageOptimizer()
        total_processed = 0
        total_optimized = 0
        total_space_saved = 0

        # Process each app
        if app_name in ["all", "fauna"]:
            processed, optimized, space_saved = self._optimize_fauna_images(
                optimizer, dry_run, force, batch_size
            )
            total_processed += processed
            total_optimized += optimized
            total_space_saved += space_saved

        if app_name in ["all", "locations"]:
            processed, optimized, space_saved = self._optimize_location_images(
                optimizer, dry_run, force, batch_size
            )
            total_processed += processed
            total_optimized += optimized
            total_space_saved += space_saved

        if app_name in ["all", "image_processing"]:
            processed, optimized, space_saved = self._optimize_image_processing_images(
                optimizer, dry_run, force, batch_size
            )
            total_processed += processed
            total_optimized += optimized
            total_space_saved += space_saved

        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Optimization complete!\n"
                f"   📊 Images processed: {total_processed}\n"
                f"   🖼️ Images optimized: {total_optimized}\n"
                f"   💾 Space saved: {self._format_bytes(total_space_saved)}\n"
                f"   📈 Savings: {self._calculate_percentage(total_space_saved, total_processed * 1024 * 500)}%"
            )
        )

    def _optimize_fauna_images(self, optimizer, dry_run, force, batch_size):
        """Optimize fauna species images."""
        try:
            from apps.fauna.models import Species
        except ImportError:
            self.stdout.write(self.style.WARNING("⚠️ Fauna app not available"))
            return 0, 0, 0

        self.stdout.write("🔬 Optimizing fauna species images...")

        # Query for species with images
        query = Species.objects.exclude(image__isnull=True).exclude(image="")

        if not force:
            query = query.filter(
                Q(optimization_status__isnull=True) |
                Q(optimization_status__in=['pending', 'failed'])
            )

        species_list = list(query[:batch_size])
        return self._process_images(species_list, optimizer, "fauna", dry_run)

    def _optimize_location_images(self, optimizer, dry_run, force, batch_size):
        """Optimize location site images."""
        try:
            from apps.locations.models import Site
        except ImportError:
            self.stdout.write(self.style.WARNING("⚠️ Locations app not available"))
            return 0, 0, 0

        self.stdout.write("📍 Optimizing location site images...")

        # Query for sites with images
        query = Site.objects.exclude(image__isnull=True).exclude(image="")

        if not force:
            query = query.filter(
                Q(optimization_status__isnull=True) |
                Q(optimization_status__in=['pending', 'failed'])
            )

        sites_list = list(query[:batch_size])
        return self._process_images(sites_list, optimizer, "locations", dry_run)

    def _optimize_image_processing_images(self, optimizer, dry_run, force, batch_size):
        """Optimize image processing uploads."""
        try:
            from apps.image_processing.models import ImageUpload
        except ImportError:
            self.stdout.write(self.style.WARNING("⚠️ Image processing app not available"))
            return 0, 0, 0

        self.stdout.write("🖼️ Optimizing image processing uploads...")

        # Query for uploads with images that aren't optimized
        query = ImageUpload.objects.filter(
            upload_status='PROCESSED'
        ).exclude(image_file__isnull=True).exclude(image_file="")

        if not force:
            query = query.filter(
                Q(is_compressed=False) |
                Q(compressed_size__isnull=True)
            )

        uploads_list = list(query[:batch_size])
        return self._process_legacy_images(uploads_list, optimizer, dry_run)

    def _process_images(self, objects_list, optimizer, app_name, dry_run):
        """Process a list of objects with OptimizableImageMixin."""
        processed = 0
        optimized = 0
        space_saved = 0

        for obj in objects_list:
            try:
                if dry_run:
                    self.stdout.write(
                        f"   📋 Would optimize: {obj.__class__.__name__} {obj.pk} - {obj.image.name if hasattr(obj, 'image') and obj.image else 'No image'}"
                    )
                    processed += 1
                    continue

                # Trigger optimization
                if hasattr(obj, 'reoptimize_images'):
                    success = obj.reoptimize_images()
                    if success:
                        optimized += 1
                        # Estimate space savings (rough calculation)
                        if hasattr(obj, 'original_size') and hasattr(obj, 'optimized_size'):
                            if obj.original_size and obj.optimized_size:
                                space_saved += (obj.original_size - obj.optimized_size)

                processed += 1

                if processed % 5 == 0:
                    self.stdout.write(f"   📊 Processed {processed} images...")

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"   ❌ Failed to optimize {obj.__class__.__name__} {obj.pk}: {e}")
                )

        return processed, optimized, space_saved

    def _process_legacy_images(self, uploads_list, optimizer, dry_run):
        """Process legacy ImageUpload objects."""
        processed = 0
        optimized = 0
        space_saved = 0

        for upload in uploads_list:
            try:
                if dry_run:
                    self.stdout.write(
                        f"   📋 Would optimize: ImageUpload {upload.pk} - {upload.image_file.name}"
                    )
                    processed += 1
                    continue

                # Read original image
                with upload.image_file.open('rb') as f:
                    original_content = f.read()

                # Optimize for web
                optimized_content = optimizer.optimize_for_web(original_content)

                if optimized_content:
                    # Save optimized version
                    from django.core.files.base import ContentFile
                    from django.utils import timezone

                    filename = f"{upload.pk}_optimized.webp"
                    upload.optimized_image.save(
                        filename,
                        ContentFile(optimized_content),
                        save=False
                    )

                    # Update metadata
                    upload.is_compressed = True
                    upload.compressed_size = len(optimized_content)
                    upload.save()

                    optimized += 1
                    space_saved += (len(original_content) - len(optimized_content))

                processed += 1

                if processed % 5 == 0:
                    self.stdout.write(f"   📊 Processed {processed} images...")

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"   ❌ Failed to optimize ImageUpload {upload.pk}: {e}")
                )

        return processed, optimized, space_saved

    def _format_bytes(self, bytes_count):
        """Format bytes into human readable format."""
        if bytes_count == 0:
            return "0 B"

        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_count < 1024.0:
                return ".1f"
            bytes_count /= 1024.0
        return ".1f"

    def _calculate_percentage(self, saved, original):
        """Calculate percentage saved."""
        if original == 0:
            return 0
        return round((saved / original) * 100, 1)
