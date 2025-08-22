from django.core.management.base import BaseCommand
from apps.image_processing.models import ImageUpload
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Clean up stuck image uploads that are in UPLOADING status'

    def add_arguments(self, parser):
        parser.add_argument(
            '--older-than',
            type=int,
            default=1,
            help='Delete uploads older than X hours (default: 1)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )

    def handle(self, *args, **options):
        older_than_hours = options['older_than']
        dry_run = options['dry_run']
        
        # Find stuck uploads
        cutoff_time = timezone.now() - timedelta(hours=older_than_hours)
        stuck_uploads = ImageUpload.objects.filter(
            upload_status=ImageUpload.UploadStatus.UPLOADING,
            uploaded_at__lt=cutoff_time
        )
        
        count = stuck_uploads.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('No stuck uploads found!')
            )
            return
        
        self.stdout.write(
            f'Found {count} stuck upload(s) older than {older_than_hours} hour(s):'
        )
        
        for upload in stuck_uploads:
            self.stdout.write(
                f'  - {upload.original_filename} (ID: {upload.pk}, Date: {upload.uploaded_at})'
            )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would delete {count} stuck upload(s). Use --dry-run=False to actually delete them.'
                )
            )
        else:
            # Actually delete them
            deleted_count = 0
            for upload in stuck_uploads:
                try:
                    # Delete the file if it exists
                    if upload.image_file and hasattr(upload.image_file, 'path'):
                        import os
                        if os.path.exists(upload.image_file.path):
                            os.remove(upload.image_file.path)
                            self.stdout.write(f'Deleted file: {upload.image_file.path}')
                    
                    # Delete the database record
                    upload.delete()
                    deleted_count += 1
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Failed to delete {upload.pk}: {e}')
                    )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully cleaned up {deleted_count} stuck upload(s)!'
                )
            )
