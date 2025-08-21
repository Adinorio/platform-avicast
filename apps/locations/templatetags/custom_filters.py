from django import template

register = template.Library()

@register.filter
def sum_counts(species_observations):
    """Sum up the counts from species observations list"""
    if not species_observations:
        return 0

    total = 0
    for species in species_observations:
        if isinstance(species, dict) and 'count' in species:
            try:
                total += int(species['count'])
            except (ValueError, TypeError):
                continue
    return total
