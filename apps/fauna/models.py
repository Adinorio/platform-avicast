import uuid

from django.db import models

from apps.common.mixins.optimizable_image import OptimizableImageMixin

# Create your models here.


class Species(OptimizableImageMixin):
    class IUCNStatus(models.TextChoices):
        LEAST_CONCERN = "LC", "Least Concern"
        NEAR_THREATENED = "NT", "Near Threatened"
        VULNERABLE = "VU", "Vulnerable"
        ENDANGERED = "EN", "Endangered"
        CRITICALLY_ENDANGERED = "CR", "Critically Endangered"
        EXTINCT_IN_THE_WILD = "EW", "Extinct in the Wild"
        EXTINCT = "EX", "Extinct"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True, help_text="Common name of the species")
    scientific_name = models.CharField(max_length=255, unique=True, help_text="Scientific name of the species")
    family = models.CharField(max_length=100, blank=True, help_text="Taxonomic family (e.g., Ardeidae for herons)")
    iucn_status = models.CharField(max_length=2, choices=IUCNStatus.choices, help_text="IUCN conservation status")
    description = models.TextField(blank=True, help_text="Additional description or notes about the species")
    image = models.ImageField(upload_to="species_images/", blank=True, null=True, help_text="Representative image of the species")
    is_archived = models.BooleanField(default=False, help_text="Whether this species is archived")

    def __str__(self):
        return self.name

    class Meta:
        app_label = "fauna"
        verbose_name_plural = "Species"
