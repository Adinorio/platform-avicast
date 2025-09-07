# Generated manually to add overridden_count field

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("image_processing", "0004_add_total_detections"),
    ]

    operations = [
        migrations.AddField(
            model_name="imageprocessingresult",
            name="overridden_count",
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
