"""
Management command to add new bird families to the system
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import migrations, models
from django.conf import settings
import os
import re


class Command(BaseCommand):
    help = 'Add new bird families to the system'

    def add_arguments(self, parser):
        parser.add_argument(
            'family_name',
            type=str,
            help='Name of the new bird family (e.g., "Penguins")'
        )
        parser.add_argument(
            '--display-name',
            type=str,
            help='Display name for the family (defaults to family_name)'
        )
        parser.add_argument(
            '--value',
            type=str,
            help='Value for the family choice (defaults to uppercase family_name)'
        )
        parser.add_argument(
            '--scientific',
            type=str,
            help='Scientific family name (e.g., "Spheniscidae")'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be added without making changes'
        )

    def handle(self, *args, **options):
        family_name = options['family_name']
        display_name = options['display_name'] or family_name
        value = options['value'] or family_name.upper().replace(' ', '_')
        scientific = options['scientific']
        dry_run = options['dry_run']

        self.stdout.write(f"Adding Bird Family: {family_name}")
        self.stdout.write("=" * 40)

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))

        # Validate input
        if not re.match(r'^[A-Za-z\s&,\-]+$', family_name):
            raise CommandError("Family name can only contain letters, spaces, &, ,, and -")

        # Generate the choice tuple
        if scientific:
            choice_value = scientific
            choice_display = f"{scientific} ({family_name})"
        else:
            choice_value = value
            choice_display = display_name

        choice_tuple = (choice_value, choice_display)

        self.stdout.write(f"Family Name: {family_name}")
        self.stdout.write(f"Choice Value: {choice_value}")
        self.stdout.write(f"Choice Display: {choice_display}")
        self.stdout.write(f"Choice Tuple: {choice_tuple}")

        # Check if family already exists
        try:
            from apps.fauna.models import Species
            existing_choices = [choice[0] for choice in Species.BirdFamily.choices]
            
            if choice_value in existing_choices:
                raise CommandError(f"Family with value '{choice_value}' already exists!")
            
            self.stdout.write(self.style.SUCCESS("Family validation passed"))
            
        except Exception as e:
            raise CommandError(f"Error validating family: {e}")

        if not dry_run:
            # Show instructions for manual addition
            self.stdout.write("\n" + "="*40)
            self.stdout.write("MANUAL STEPS REQUIRED:")
            self.stdout.write("="*40)
            self.stdout.write("1. Edit apps/fauna/models.py")
            self.stdout.write("   Add this line to the BirdFamily class:")
            self.stdout.write(f"   {value.upper()} = \"{choice_value}\", \"{choice_display}\"")
            self.stdout.write("")
            self.stdout.write("2. Create migration:")
            self.stdout.write("   python manage.py makemigrations fauna --name add_{family_name.lower()}_family")
            self.stdout.write("")
            self.stdout.write("3. Apply migration:")
            self.stdout.write("   python manage.py migrate fauna")
            self.stdout.write("")
            self.stdout.write("4. Test the new family:")
            self.stdout.write("   python manage.py shell")
            self.stdout.write("   >>> from apps.fauna.models import Species")
            self.stdout.write("   >>> Species.BirdFamily.choices")
            self.stdout.write("")
            self.stdout.write("5. Update Excel handler (if needed):")
            self.stdout.write("   Edit apps/locations/utils/excel_handler.py")
            self.stdout.write("   Add detection patterns for the new family")
        else:
            self.stdout.write("\n" + "="*40)
            self.stdout.write("DRY RUN COMPLETE")
            self.stdout.write("="*40)
            self.stdout.write("Family would be added successfully!")
            self.stdout.write("Run without --dry-run to see manual steps")

        self.stdout.write(self.style.SUCCESS("\nOperation complete!"))

    def get_suggested_placement(self, family_name):
        """Suggest where to place the new family in the model"""
        suggestions = {
            'penguin': 'Water Birds',
            'flamingo': 'Water Birds', 
            'pelican': 'Water Birds',
            'parrot': 'Small Birds',
            'toucan': 'Small Birds',
            'hummingbird': 'Small Birds',
            'vulture': 'Raptors',
            'kite': 'Raptors',
            'eagle': 'Raptors',
            'sparrow': 'Songbirds',
            'finch': 'Songbirds',
            'canary': 'Songbirds'
        }
        
        family_lower = family_name.lower()
        for keyword, category in suggestions.items():
            if keyword in family_lower:
                return category
        
        return "Additional/Other"
