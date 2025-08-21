# Generated manually to add AI model fields

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('image_processing', '0001_initial'),
    ]

    operations = [
        # Add AIModel choices to ImageProcessingResult
        migrations.AlterField(
            model_name='imageprocessingresult',
            name='detected_species',
            field=models.CharField(blank=True, choices=[('CHINESE_EGRET', 'Chinese Egret'), ('WHISKERED_TERN', 'Whiskered Tern'), ('GREAT_KNOT', 'Great Knot')], max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='imageprocessingresult',
            name='overridden_species',
            field=models.CharField(blank=True, choices=[('CHINESE_EGRET', 'Chinese Egret'), ('WHISKERED_TERN', 'Whiskered Tern'), ('GREAT_KNOT', 'Great Knot')], max_length=50, null=True),
        ),
        # Add new AI model fields
        migrations.AddField(
            model_name='imageprocessingresult',
            name='ai_model',
            field=models.CharField(choices=[('YOLO_V5', 'YOLOv5'), ('YOLO_V8', 'YOLOv8'), ('YOLO_V9', 'YOLOv9')], default='YOLO_V8', max_length=20),
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
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=6, null=True),
        ),
        migrations.AddField(
            model_name='imageprocessingresult',
            name='model_confidence_threshold',
            field=models.DecimalField(decimal_places=2, default=0.25, max_digits=3),
        ),
        migrations.AddField(
            model_name='imageprocessingresult',
            name='reviewed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='imageprocessingresult',
            name='overridden_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
