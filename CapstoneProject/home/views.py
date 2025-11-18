from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
#from products.utils import get_top_rated_movies
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from .models import Recipe, Interaction
from django.db.models import Avg, Count, Q
from django.http import JsonResponse
from django.contrib import messages
from .forms import EditProfileForm
from django.conf import settings
from django.db import models
from openai import OpenAI
import os, json

client = OpenAI(api_key=settings.OPENAI_API_KEY)


def chefgpt(request):
    if request.method == "POST":
        question = request.POST.get("question", "").strip()

        if not question:
            return JsonResponse({"error": "Empty question"}, status=400)

        # --- Step 1️⃣: Do a broad search for possible matches ---
        initial_matches = Recipe.objects.filter(
            Q(name__icontains=question) |
            Q(description__icontains=question)
        )

        # --- Step 2️⃣: Fallback — search manually in JSON-like fields ---
        related_recipes = list(initial_matches)
        question_lower = question.lower()

        for recipe in Recipe.objects.all():
            # Skip duplicates
            if recipe in related_recipes:
                continue

            # Check inside ingredients, tags
            ingredients = " ".join(recipe.get_ingredients()).lower()
            tags = " ".join(recipe.get_tags()).lower()

            if question_lower in ingredients or question_lower in tags:
                related_recipes.append(recipe)

        # Limit to top 5
        related_recipes = related_recipes[:5]

        # --- Step 3️⃣: Handle no matches ---
        if not related_recipes:
            return JsonResponse({
                "answer": "I couldn’t find any matching recipes in our database."
            })

        # --- Step 4️⃣: Build database context for GPT ---
        recipe_summaries = []
        for r in related_recipes:
            ingredients = ", ".join(r.get_ingredients()[:5])
            recipe_summaries.append(
                f"{r.name} — {r.description[:100]}... | Ingredients: {ingredients}"
            )

        database_context = "\n".join(recipe_summaries)

        # --- Step 5️⃣: Ask GPT, but constrain it to the DB context ---
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are ChefGPT, a cooking assistant that only uses recipes "
                            "from the provided internal database. Do not make up new recipes. "
                            "If asked for a recipe, base your answer strictly on the database entries below.\n\n"
                            f"Available recipes:\n{database_context}"
                        ),
                    },
                    {"role": "user", "content": question},
                ],
                max_tokens=300,
            )

            answer = response.choices[0].message.content
            return JsonResponse({"answer": answer})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home:index')  # Redirect to home page after successful login
        else:
            return render(request, 'home/login.html', {'error': 'Invalid credentials'})
    return render(request, 'home/login.html')


def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        
        # Check if passwords match
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'home/register.html')
        
        # Check if the username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return render(request, 'home/register.html')

        # Check if the email is already in use
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email is already in use.")
            return render(request, 'home/register.html')

        # Create the user
        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            user.save()
            messages.success(request, "Registration successful. You can now log in.")
            return redirect('home:login')  # Redirect to the login page
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return render(request, 'home/register.html')

    # Render the registration page for GET requests
    return render(request, 'home/register.html')



def home(request):
    # Annotate recipes with avg rating + number of reviews
    all_recipes = (
        Recipe.objects.annotate(
            avg_rating=Avg('interactions__rating'),
            review_count=Count('interactions')
        )
        .order_by('-avg_rating', '-review_count')
    )

    # --- Collect all unique ingredients ---
    all_ingredients = set()
    for recipe in Recipe.objects.all():
        for ing in recipe.get_ingredients():
            ing = ing.strip().capitalize()
            all_ingredients.add(ing)

    # Paginate — show 10 recipes per page
    paginator = Paginator(all_recipes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'all_ingredients': sorted(all_ingredients),
    }

    return render(request, 'home/index.html', context)

def recipe(request, recipe_id):
    recipe = get_object_or_404(Recipe, recipe_id=recipe_id)
    interactions = Interaction.objects.filter(recipe=recipe).order_by('-date')

    # Parse JSON fields for display
    nutrition = recipe.get_nutrition()
    ingredients = recipe.get_ingredients()
    steps = recipe.get_steps()
    tags = recipe.get_tags()

    return render(request, 'home/recipe.html', {
        'recipe': recipe,
        'nutrition': nutrition,
        'ingredients': ingredients,
        'steps': steps,
        'tags': tags,
        'interactions': interactions,
    })

@require_GET
def load_recipes(request):
    # Get top-rated recipes (or however you want to sort them)
    recipes = (
        Recipe.objects.annotate(
            avg_rating=Avg('interactions__rating'),
            review_count=Count('interactions')
        )
        .order_by('-avg_rating', '-review_count')[:10]
    )

    # Return JSON data
    data = [
        {
            "id": recipe.recipe_id,
            "name": recipe.name,
            "rating": round(recipe.avg_rating or 0, 2),
            "review_count": recipe.review_count,
        }
        for recipe in recipes
    ]

    return JsonResponse({"recipes": data})

def filter_recipes_by_ingredient(request):
    """
    Returns all recipes that contain a given ingredient.
    Used by AJAX when clicking an ingredient button.
    """
    if request.method == "POST":
        data = json.loads(request.body)
        ingredient = data.get("ingredient", "").strip().lower()

        if not ingredient:
            return JsonResponse({"error": "No ingredient provided"}, status=400)

        # Fetch recipes containing the ingredient
        matched_recipes = []
        for recipe in Recipe.objects.all():
            ingredients = [ing.lower() for ing in recipe.get_ingredients()]
            if any(ingredient in ing for ing in ingredients):
                matched_recipes.append({
                    "name": recipe.name,
                    "recipe_id": recipe.recipe_id,
                    "avg_rating": getattr(recipe, "avg_rating", None),
                    "review_count": recipe.interactions.count(),
                })

        return JsonResponse({"recipes": matched_recipes})

    return JsonResponse({"error": "Invalid request method"}, status=405)

@login_required
def profile(request):
    return render(request, 'home/profile.html')

@login_required
def edit_profile(request):
    if request.method == 'POST':
        user = request.user
        form = EditProfileForm(request.POST, instance=user)
        # Get password fields from the request
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        if form.is_valid():
            if password and confirm_password:  # Check if password fields are filled
                if password == confirm_password:
                    user.set_password(password)
                else:
                    messages.error(request, "Passwords do not match.")
                    return redirect('home:edit_profile')

            form.save()
            update_session_auth_hash(request, user)  # Prevent logout after password change
            messages.success(request, "Profile updated successfully.")
            return redirect('home:profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = EditProfileForm(instance=request.user)
    return render(request, 'home/edit_profile.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('home:login')