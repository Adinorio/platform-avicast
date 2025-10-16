import uuid

from django.db import models

from apps.common.mixins.optimizable_image import OptimizableImageMixin

# Create your models here.


class BirdFamily(models.Model):
    """Model for managing bird families through UI"""
    
    class FamilyCategory(models.TextChoices):
        WATER_BIRDS = "WATER_BIRDS", "Water Birds"
        LAND_BIRDS = "LAND_BIRDS", "Land Birds"
        RAPTORS = "RAPTORS", "Raptors"
        SMALL_BIRDS = "SMALL_BIRDS", "Small Birds"
        SONGBIRDS = "SONGBIRDS", "Songbirds"
        SCIENTIFIC = "SCIENTIFIC", "Scientific Families"
        OTHER = "OTHER", "Other"
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True, help_text="Family name (e.g., HERONS AND EGRETS)")
    display_name = models.CharField(max_length=100, help_text="Display name (e.g., Herons and Egrets)")
    category = models.CharField(max_length=20, choices=FamilyCategory.choices, default=FamilyCategory.WATER_BIRDS)
    description = models.TextField(blank=True, help_text="Description of this family")
    scientific_name = models.CharField(max_length=100, blank=True, help_text="Scientific family name (optional)")
    is_active = models.BooleanField(default=True, help_text="Whether this family is available for selection")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.display_name
    
    class Meta:
        app_label = "fauna"
        verbose_name = "Bird Family"
        verbose_name_plural = "Bird Families"
        ordering = ['category', 'display_name']


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
    family = models.ForeignKey('BirdFamily', on_delete=models.SET_NULL, null=True, blank=True, help_text="Bird family classification")
    iucn_status = models.CharField(max_length=2, choices=IUCNStatus.choices, help_text="IUCN conservation status")
    description = models.TextField(blank=True, help_text="Additional description or notes about the species")
    image = models.ImageField(upload_to="species_images/", blank=True, null=True, help_text="Representative image of the species")
    is_archived = models.BooleanField(default=False, help_text="Whether this species is archived")

    def save(self, *args, **kwargs):
        """Override save to update related text fields when name changes"""
        # Check if this is an update and if the name changed
        if self.pk:
            try:
                old_species = Species.objects.get(pk=self.pk)
                if old_species.name != self.name:
                    # Name changed, update related text fields
                    self._update_related_text_fields(old_species.name, self.name)
            except Species.DoesNotExist:
                pass  # New species, no need to update
        
        super().save(*args, **kwargs)
    
    def _update_related_text_fields(self, old_name, new_name):
        """Update text fields in related models when species name changes"""
        try:
            # Update CensusObservation.species_name field
            from apps.locations.models import CensusObservation
            
            updated_count = CensusObservation.objects.filter(
                species=self,
                species_name=old_name
            ).update(species_name=new_name)
            
            if updated_count > 0:
                print(f"Updated {updated_count} census observations from '{old_name}' to '{new_name}'")
                
        except Exception as e:
            print(f"Error updating related text fields: {e}")
    
    def __str__(self):
        return self.name

    class Meta:
        app_label = "fauna"
        verbose_name_plural = "Species"
