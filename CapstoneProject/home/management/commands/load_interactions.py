import csv
from django.core.management.base import BaseCommand
from home.models import Recipe, Interaction
from datetime import datetime

class Command(BaseCommand):
    help = "Load interactions (reviews) from RAW_interactions.csv"

    def handle(self, *args, **kwargs):
        with open("RAW_interactions.csv", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            count = 0
            for row in reader:
                try:
                    recipe = Recipe.objects.get(recipe_id=int(row["recipe_id"]))
                except Recipe.DoesNotExist:
                    continue  # skip reviews where recipe is missing

                Interaction.objects.update_or_create(
                    user_id=int(row["user_id"]),
                    recipe=recipe,
                    date=datetime.strptime(row["date"], "%Y-%m-%d").date(),
                    defaults={
                        "rating": int(row["rating"]),
                        "review": row["review"],
                    }
                )
                count += 1

        self.stdout.write(self.style.SUCCESS(f"Loaded {count} interactions successfully."))