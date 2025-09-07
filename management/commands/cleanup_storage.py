"""
Django management command to cleanup old image files and optimize storage
Usage: python manage.py cleanup_storage --days=30 --dry-run
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.image_processing.cloud_storage import get_storage_backend


class Command(BaseCommand):
    help = "Cleanup old image files and optimize storage usage"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Files older than this many days will be archived (default: 30)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be cleaned up without actually doing it",
        )
        parser.add_argument(
            "--force", action="store_true", help="Force cleanup even if not near storage limits"
        )
        parser.add_argument(
            "--optimize-images",
            action="store_true",
            help="Re-optimize existing uncompressed images",
        )

    def handle(self, *args, **options):
        days = options["days"]
        dry_run = options["dry_run"]
        force = options["force"]
        optimize_images = options["optimize_images"]

        self.stdout.write(self.style.SUCCESS(f"🧹 Starting storage cleanup (dry_run={dry_run})"))

        # Get current storage usage
        storage_backend = get_storage_backend()
        if hasattr(storage_backend, "check_storage_usage"):
            usage_info = storage_backend.check_storage_usage()
            self.stdout.write(f"📊 Current storage usage: {usage_info['avicast_usage_mb']:.2f} MB")
            self.stdout.write(f"📈 Usage percentage: {usage_info['usage_percentage']:.1f}%")

            if usage_info["near_limit"] or force:
                self.stdout.write(
                    self.style.WARNING("⚠️  Near storage limit, proceeding with cleanup...")
                )
            elif not force:
                self.stdout.write(
                    self.style.SUCCESS(
                        "✅ Storage usage is within limits, use --force to cleanup anyway"
                    )
                )
                return

        # Cleanup old files
        if dry_run:
            self.stdout.write("🔍 DRY RUN - No files will be deleted")
            # Show what would be deleted
            from apps.image_processing.models import ImageUpload

            cutoff_date = timezone.now() - timedelta(days=days)
            old_files = ImageUpload.objects.filter(uploaded_at__lt=cutoff_date, storage_tier="HOT")
            total_size = sum(f.file_size for f in old_files)
            self.stdout.write(f"📁 Would archive {old_files.count()} files")
            self.stdout.write(f"💾 Would free {total_size / (1024*1024):.2f} MB")
        else:
            deleted_count, freed_space = storage_backend.cleanup_old_files(days)
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Archived {deleted_count} files, freed {freed_space / (1024*1024):.2f} MB"
                )
            )

        # Optimize uncompressed images
        if optimize_images:
            self.stdout.write("🎨 Optimizing uncompressed images...")
            self._optimize_uncompressed_images(dry_run)

        # Show final storage statistics
        if hasattr(storage_backend, "check_storage_usage"):
            final_usage = storage_backend.check_storage_usage()
            self.stdout.write(
                self.style.SUCCESS(
                    f"📊 Final storage usage: {final_usage['avicast_usage_mb']:.2f} MB "
                    f"({final_usage['usage_percentage']:.1f}%)"
                )
            )

        self.stdout.write(self.style.SUCCESS("🎉 Storage cleanup completed!"))

    def _optimize_uncompressed_images(self, dry_run=False):
        """Optimize images that haven't been compressed yet"""
        from apps.image_processing.image_optimizer import ImageOptimizer
        from apps.image_processing.models import ImageUpload

        uncompressed = ImageUpload.objects.filter(is_compressed=False)

        if dry_run:
            self.stdout.write(f"🔍 Would optimize {uncompressed.count()} uncompressed images")
            return

        optimized_count = 0
        space_saved = 0

        for image_obj in uncompressed:
            try:
                if image_obj.image_file and hasattr(image_obj.image_file, "path"):
                    # Read original file
                    with open(image_obj.image_file.path, "rb") as f:
                        original_size = image_obj.file_size

                        # Optimize
                        optimized_content, new_size, format_used = ImageOptimizer.optimize_image(f)

                        # Save optimized version
                        from django.core.files.base import ContentFile

                        optimized_file = ContentFile(optimized_content, image_obj.original_filename)

                        # Update database record
                        image_obj.image_file.save(
                            image_obj.original_filename, optimized_file, save=False
                        )
                        image_obj.compressed_size = new_size
                        image_obj.is_compressed = True
                        image_obj.save()

                        optimized_count += 1
                        space_saved += original_size - new_size

                        if optimized_count % 10 == 0:
                            self.stdout.write(f"📈 Optimized {optimized_count} images...")

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Failed to optimize {image_obj.id}: {e}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Optimized {optimized_count} images, saved {space_saved / (1024*1024):.2f} MB"
            )
        )
