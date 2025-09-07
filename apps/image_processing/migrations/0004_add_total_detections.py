# Generated manually to add total_detections field

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("image_processing", "0003_add_missing_storage_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="imageprocessingresult",
            name="total_detections",
            field=models.IntegerField(default=0, help_text="Number of birds detected"),
        ),
    ]
