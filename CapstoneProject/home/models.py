from django.db import models
import json, ast

class Recipe(models.Model):
    name = models.CharField(max_length=255)
    recipe_id = models.IntegerField(unique=True)
    minutes = models.IntegerField()
    contributor_id = models.IntegerField()
    submitted = models.DateField()
    tags = models.TextField()          # JSON string of tags
    nutrition = models.TextField()     # JSON string of nutrition values
    n_steps = models.IntegerField()
    steps = models.TextField()         # JSON string list of instructions
    description = models.TextField()
    ingredients = models.TextField()   # JSON string list of ingredients
    n_ingredients = models.IntegerField()

    def get_tags(self):
        try:
            return json.loads(self.tags)
        except json.JSONDecodeError:
            try:
                # Try Python literal evaluation (handles ['...'] cases)
                return ast.literal_eval(self.tags)
            except Exception:
                return []  # fallback
            
    def get_nutrition(self):
        if not self.nutrition:
            return []
        try:
            return json.loads(self.nutrition)
        except json.JSONDecodeError:
            try:
                return ast.literal_eval(self.nutrition)
            except Exception:
                return []

    def get_nutrition_info(self):
        try:
            values = self.get_nutrition()
            labels = [
                "Calories (kcal)",
                "Total Fat (%DV)",
                "Sugar (%DV)",
                "Sodium (%DV)",
                "Protein (%DV)",
                "Saturated Fat (%DV)"
            ]

            # Handle missing or extra values gracefully
            nutrition_data = []
            for label, value in zip(labels, values):
                nutrition_data.append((label, value))
            return nutrition_data

        except Exception:
            return []

    def get_steps(self):
        try:
            return json.loads(self.steps)
        except json.JSONDecodeError:
            try:
                return ast.literal_eval(self.steps)
            except Exception:
                return []

    def get_ingredients(self):
        try:
            return json.loads(self.ingredients)
        except json.JSONDecodeError:
            try:
                return ast.literal_eval(self.ingredients)
            except Exception:
                return []


class Interaction(models.Model):
    user_id = models.IntegerField()
    recipe = models.ForeignKey("Recipe", on_delete=models.CASCADE, related_name="interactions")
    date = models.DateField()
    rating = models.IntegerField()
    review = models.TextField()

    def __str__(self):
        return f"Review by User {self.user_id} for Recipe {self.recipe.name} (Rating: {self.rating})"