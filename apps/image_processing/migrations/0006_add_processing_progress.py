# Generated manually for processing progress tracking

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("image_processing", "0005_add_overridden_count"),
    ]

    operations = [
        migrations.AddField(
            model_name="imageupload",
            name="processing_step",
            field=models.CharField(
                blank=True,
                choices=[
                    ("READING_FILE", "Reading image file"),
                    ("OPTIMIZING", "Optimizing image"),
                    ("DETECTING", "Detecting birds"),
                    ("SAVING", "Saving results"),
                    ("COMPLETE", "Processing complete"),
                ],
                default="",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="imageupload",
            name="processing_progress",
            field=models.IntegerField(default=0, help_text="Progress percentage (0-100)"),
        ),
    ]
