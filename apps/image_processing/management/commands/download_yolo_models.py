"""
Management command to download YOLO models for bird detection.

This command downloads the base YOLO models (v5, v8, v9) that can be used
for bird detection when custom trained models are not available.
"""

from django.core.management.base import BaseCommand
from django.conf import settings
import os
import requests
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Download YOLO models for bird detection'

    def add_arguments(self, parser):
        parser.add_argument(
            '--models',
            nargs='+',
            choices=['v5', 'v8', 'v9', 'all'],
            default=['all'],
            help='Specific YOLO versions to download (v5, v8, v9, or all)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force download even if models already exist'
        )

    def handle(self, *args, **options):
        models_to_download = options['models']
        force = options['force']
        
        if 'all' in models_to_download:
            models_to_download = ['v5', 'v8', 'v9']
        
        self.stdout.write(
            self.style.SUCCESS('Starting YOLO model download...')
        )
        
        # Create models directory if it doesn't exist
        # Import configuration
        from apps.image_processing.config import YOLO_MODEL_CONFIG

        models_dir = Path(settings.BASE_DIR) / 'models'
        models_dir.mkdir(exist_ok=True)

        # Use configuration for YOLO model details
        yolo_models = YOLO_MODEL_CONFIG
        
        downloaded_count = 0
        skipped_count = 0
        error_count = 0
        
        for version in models_to_download:
            if version not in yolo_models:
                self.stdout.write(
                    self.style.WARNING(f'Unknown version: {version}')
                )
                continue
            
            model_info = yolo_models[version]
            model_path = models_dir / model_info['filename']
            
            # Check if model already exists
            if model_path.exists() and not force:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  {model_info["filename"]} already exists, skipping...')
                )
                skipped_count += 1
                continue
            
            self.stdout.write(f'Downloading YOLO{version.upper()}...')
            self.stdout.write(f'  URL: {model_info["url"]}')
            self.stdout.write(f'  Size: ~{model_info["size_mb"]} MB')
            self.stdout.write(f'  Path: {model_path}')
            
            try:
                # Download the model
                response = requests.get(model_info['url'], stream=True)
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded_size = 0
                
                with open(model_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            
                            # Show progress
                            if total_size > 0:
                                progress = (downloaded_size / total_size) * 100
                                self.stdout.write(f'\r  Progress: {progress:.1f}%', ending='')
                
                self.stdout.write('')  # New line after progress
                
                # Verify file size
                actual_size = model_path.stat().st_size
                if actual_size > 0:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ YOLO{version.upper()} downloaded successfully!')
                    )
                    # Import utility function
                    from apps.image_processing.config import calculate_file_size_mb
                    self.stdout.write(f'  File size: {calculate_file_size_mb(actual_size):.1f} MB')
                    downloaded_count += 1
                else:
                    raise Exception("Downloaded file is empty")
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error downloading YOLO{version.upper()}: {e}')
                )
                error_count += 1
                
                # Remove failed download
                if model_path.exists():
                    model_path.unlink()
        
        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write('DOWNLOAD SUMMARY')
        self.stdout.write('='*50)
        self.stdout.write(f'Models downloaded: {downloaded_count}')
        self.stdout.write(f'Models skipped: {skipped_count}')
        self.stdout.write(f'Errors: {error_count}')
        
        if downloaded_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'\nSuccessfully downloaded {downloaded_count} YOLO model(s)!')
            )
            self.stdout.write(
                self.style.SUCCESS('You can now use these models for bird detection.')
            )
        
        if error_count > 0:
            self.stdout.write(
                self.style.WARNING(f'\n{error_count} model(s) failed to download.')
            )
            self.stdout.write(
                self.style.WARNING('Check your internet connection and try again.')
            )
        
        # Next steps
        self.stdout.write('\n' + '='*50)
        self.stdout.write('NEXT STEPS')
        self.stdout.write('='*50)
        self.stdout.write('1. Go to AI Models page to select your preferred model')
        self.stdout.write('2. Upload images for bird detection')
        self.stdout.write('3. The system will automatically use the selected model')
        self.stdout.write('4. You can benchmark models to compare performance')
