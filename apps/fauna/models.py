import uuid

from django.db import models

# Create your models here.


class Species(models.Model):
    class IUCNStatus(models.TextChoices):
        LEAST_CONCERN = "LC", "Least Concern"
        NEAR_THREATENED = "NT", "Near Threatened"
        VULNERABLE = "VU", "Vulnerable"
        ENDANGERED = "EN", "Endangered"
        CRITICALLY_ENDANGERED = "CR", "Critically Endangered"
        EXTINCT_IN_THE_WILD = "EW", "Extinct in the Wild"
        EXTINCT = "EX", "Extinct"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    scientific_name = models.CharField(max_length=255, unique=True)
    iucn_status = models.CharField(max_length=2, choices=IUCNStatus.choices)
    image = models.ImageField(upload_to="species_images/", blank=True, null=True)
    is_archived = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        app_label = "fauna"
        verbose_name_plural = "Species"
