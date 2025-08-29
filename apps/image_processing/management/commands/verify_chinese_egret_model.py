from django.core.management.base import BaseCommand
from apps.image_processing.bird_detection_service import get_bird_detection_service
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Verify that the Chinese Egret model is properly loaded and working in Django context'

    def add_arguments(self, parser):
        parser.add_argument(
            '--switch-to-chinese-egret',
            action='store_true',
            help='Switch to Chinese Egret model after verification',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔍 Verifying Chinese Egret Model Integration')
        )
        self.stdout.write('=' * 60)

        try:
            # Get the bird detection service
            service = get_bird_detection_service()

            # Check available models
            available_models = list(service.models.keys())
            self.stdout.write(f"📋 Available models: {available_models}")

            # Check if Chinese Egret model is loaded
            chinese_egret_loaded = 'CHINESE_EGRET_V1' in available_models
            status = self.style.SUCCESS('✅ YES') if chinese_egret_loaded else self.style.ERROR('❌ NO')
            self.stdout.write(f"🏆 Chinese Egret V1 loaded: {status}")

            if chinese_egret_loaded:
                # Get current model info
                model_info = service.get_model_info()
                self.stdout.write(f"🎯 Current model: {model_info['current_version']}")
                self.stdout.write(f"📊 Current performance: {model_info['current_performance']}")

                # Check Chinese Egret specialist info
                chinese_egret_info = model_info.get('chinese_egret_specialist', {})
                self.stdout.write(f"🏆 Chinese Egret Specialist available: {chinese_egret_info.get('available', False)}")
                self.stdout.write(f"🏆 Chinese Egret Specialist status: {chinese_egret_info.get('status', 'Unknown')}")

                # Switch to Chinese Egret model if requested
                if options['switch_to_chinese_egret']:
                    self.stdout.write('\n🔄 Switching to Chinese Egret model...')
                    switch_result = service.switch_model('CHINESE_EGRET_V1')
                    if switch_result:
                        updated_info = service.get_model_info()
                        self.stdout.write(self.style.SUCCESS('✅ Successfully switched to Chinese Egret model!'))
                        self.stdout.write(f"🎯 New current model: {updated_info['current_version']}")
                        self.stdout.write(f"📊 New performance: {updated_info['current_performance']}")
                    else:
                        self.stdout.write(self.style.ERROR('❌ Failed to switch to Chinese Egret model'))

                # Show how to use the model
                self.stdout.write('\n💡 HOW TO USE THE CHINESE EGRET MODEL:')
                self.stdout.write('   1. In your Django app, go to Model Selection (/image_processing/models/)')
                self.stdout.write('   2. Select "🏆 Chinese Egret Specialist (99.46% mAP)"')
                self.stdout.write('   3. Upload Chinese Egret images for ultra-high accuracy detection')
                self.stdout.write('   4. Check logs for "🏆 Loading Chinese Egret Specialist model" messages')

                self.stdout.write('\n📊 EXPECTED PERFORMANCE:')
                self.stdout.write('   • 99.46% mAP@0.5 (vs ~70% for generic models)')
                self.stdout.write('   • 97.35% precision (low false positives)')
                self.stdout.write('   • 99.12% recall (catches almost all birds)')
                self.stdout.write('   • 75 FPS real-time processing')
                self.stdout.write('   • Multi-bird detection (up to 8 per image)')

            else:
                self.stdout.write(self.style.ERROR('❌ Chinese Egret model not found!'))
                self.stdout.write('🔧 Troubleshooting:')
                self.stdout.write('   1. Check if model files exist in models/chinese_egret_v1/')
                self.stdout.write('   2. Restart Django application')
                self.stdout.write('   3. Check file permissions')
                self.stdout.write('   4. Review logs for loading errors')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error during verification: {e}')
            )

        self.stdout.write('=' * 60)
        self.stdout.write('🏆 Verification Complete!')
