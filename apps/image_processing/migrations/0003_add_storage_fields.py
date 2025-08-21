# Generated manually to add storage fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('image_processing', '0002_add_ai_model_fields'),
    ]

    operations = [
        # Add storage tier management fields
        migrations.AddField(
            model_name='imageupload',
            name='storage_tier',
            field=models.CharField(
                choices=[
                    ('HOT', 'Hot Storage'),
                    ('WARM', 'Warm Storage'),
                    ('COLD', 'Cold Storage'),
                    ('ARCHIVE', 'Archive')
                ],
                default='HOT',
                help_text='Storage tier for lifecycle management',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='imageupload',
            name='last_accessed',
            field=models.DateTimeField(auto_now=True, help_text='Last time file was accessed'),
        ),
        migrations.AddField(
            model_name='imageupload',
            name='retention_days',
            field=models.IntegerField(default=365, help_text='Days to retain file'),
        ),
        
        # Add deduplication and optimization fields
        migrations.AddField(
            model_name='imageupload',
            name='file_hash',
            field=models.CharField(
                blank=True,
                help_text='SHA256 hash of file content',
                max_length=64,
            ),
        ),
        migrations.AddField(
            model_name='imageupload',
            name='is_compressed',
            field=models.BooleanField(
                default=False,
                help_text='Whether image has been optimized',
            ),
        ),
        migrations.AddField(
            model_name='imageupload',
            name='compressed_size',
            field=models.BigIntegerField(
                blank=True,
                help_text='Size after compression',
                null=True,
            ),
        ),
        
        # Add archive storage field
        migrations.AddField(
            model_name='imageupload',
            name='archive_path',
            field=models.CharField(
                blank=True,
                help_text='Path to archived file',
                max_length=500,
                null=True,
            ),
        ),
        
        # Add AI model fields to ImageProcessingResult
        migrations.AddField(
            model_name='imageprocessingresult',
            name='ai_model',
            field=models.CharField(
                choices=[
                    ('YOLO_V5', 'YOLOv5'),
                    ('YOLO_V8', 'YOLOv8'),
                    ('YOLO_V9', 'YOLOv9')
                ],
                default='YOLO_V8',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='imageprocessingresult',
            name='model_version',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='imageprocessingresult',
            name='processing_device',
            field=models.CharField(default='cpu', max_length=20),
        ),
        migrations.AddField(
            model_name='imageprocessingresult',
            name='inference_time',
            field=models.DecimalField(
                blank=True,
                decimal_places=3,
                help_text='in seconds',
                max_digits=6,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='imageprocessingresult',
            name='model_confidence_threshold',
            field=models.DecimalField(
                decimal_places=2,
                default=0.25,
                max_digits=3,
            ),
        ),
    ]
