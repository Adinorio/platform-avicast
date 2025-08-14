import uuid
from django.db import models
from django.conf import settings

# Create your models here.

class Site(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    location_desc = models.TextField(blank=True)
    # coordinates = models.PointField(blank=True, null=True) # Requires GeoDjango
    image = models.ImageField(upload_to='site_images/', blank=True, null=True)
    is_archived = models.BooleanField(default=False)
    species = models.ManyToManyField(
        'fauna.Species',
        through='BirdCensus',
        related_name='sites'
    )

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'locations'

class BirdCensus(models.Model):
    class Source(models.TextChoices):
        MANUAL = 'MANUAL', 'Manual'
        IMAGE_PROCESSING = 'IMAGE_PROCESSING', 'Image Processing'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    species = models.ForeignKey('fauna.Species', on_delete=models.CASCADE)
    count = models.PositiveIntegerField()
    census_date = models.DateField()
    source = models.CharField(max_length=20, choices=Source.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )

    def __str__(self):
        return f"{self.count} {self.species} at {self.site} on {self.census_date}"

    class Meta:
        app_label = 'locations'
        unique_together = ('site', 'species', 'census_date', 'source')
        verbose_name_plural = "Bird Censuses"
