import csv
import json
from django.core.management.base import BaseCommand
from home.models import Recipe
from datetime import datetime

class Command(BaseCommand):
    help = 'Load recipes from RAW_recipes.csv'

    def handle(self, *args, **kwargs):
        with open('RAW_recipes.csv', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                Recipe.objects.update_or_create(
                    recipe_id=int(row['id']),
                    defaults={
                        'name': row['name'],
                        'minutes': int(row['minutes']),
                        'contributor_id': int(row['contributor_id']),
                        'submitted': datetime.strptime(row['submitted'], "%Y-%m-%d").date(),
                        'tags': row['tags'],
                        'nutrition': row['nutrition'],
                        'n_steps': int(row['n_steps']),
                        'steps': row['steps'],
                        'description': row['description'],
                        'ingredients': row['ingredients'],
                        'n_ingredients': int(row['n_ingredients']),
                    }
                )
        self.stdout.write(self.style.SUCCESS('Recipes loaded successfully'))
