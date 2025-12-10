from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
#from products.utils import get_top_rated_movies
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from .models import Recipe, Interaction, Favorite
from django.db.models import Avg, Count, Q
from django.http import JsonResponse
from django.contrib import messages
from .forms import EditProfileForm, ReviewForm
from django.conf import settings
from django.db import models
from datetime import date
from openai import OpenAI
import random, re, json


def get_openai_client():
    return OpenAI(api_key=settings.OPENAI_API_KEY)

def chefgpt(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    question = request.POST.get("question", "").strip()
    if not question:
        return JsonResponse({"error": "Empty question"}, status=400)
    
    query = question.lower()

    # Remove common user phrasing around recipe requests
    query = re.sub(
        r"(hello | give me a|i want a|show me a|recipe for|please make|can you make|make me|provide|suggest|i have|i am allergic to)\s+",
        "",
        query
    )
    query = query.replace("recipe", "").strip()

    #Extract requested ingredients from question
    ingredient_pattern = re.search(r"(?:with|ingredients?:)\s*(.+)", question, re.IGNORECASE)
    requested_ingredients = []
    if ingredient_pattern:
        requested_ingredients = [i.strip().lower() for i in ingredient_pattern.group(1).split(",")]

    #Pre-filter recipes
    matching_recipes = []

    for recipe in Recipe.objects.all():
        recipe_ings = [i.lower() for i in recipe.get_ingredients()]

        if requested_ingredients:
            if all(ing in recipe_ings for ing in requested_ingredients):
                matching_recipes.append(recipe)
        else:
            if (query in recipe.name.lower() or
                query in recipe.description.lower() or
                any(query in tag.lower() for tag in recipe.get_tags())):
                matching_recipes.append(recipe)

    #Rank by average rating
    def get_average_rating(recipe):
        ratings = recipe.interactions.all().values_list("rating", flat=True)
        return sum(ratings)/len(ratings) if ratings else 0

    matching_recipes.sort(key=get_average_rating, reverse=True)

    top_recipes = matching_recipes[:5]

    if not top_recipes:
        return JsonResponse({"answer": "I couldn’t find any matching recipes in our database."})

    #Build structured summaries for GPT
    recipe_summaries = []
    for r in top_recipes:
        ingredients = r.get_ingredients()
        steps = r.get_steps()
        nutrition = r.get_nutrition_info()

        #Create a structured string for GPT
        nutrition_text = ""
        if nutrition:
            nutrition_text = "\n## Nutrition (per serving)\n" + "\n".join(
                [f"- {label}: {value}" for label, value in nutrition]
            )

        recipe_summary = f"""Name: {r.name}
        Rating: {get_average_rating(r):.1f}/5
        Preparation Time: {r.minutes} minutes

        Ingredients:
        - {"\n- ".join(ingredients)}

        Description:
        {r.description}

        Steps:
        {"".join([f"{i+1}. {step}\n" for i, step in enumerate(steps)])}
        {nutrition_text}
        """
        recipe_summaries.append(recipe_summary)

    database_context = "\n\n".join(recipe_summaries)

    #Ask GPT
    try:
        client = get_openai_client()
        system_prompt = (
            "You are ChefGPT, a helpful cooking assistant. You must only reference recipes provided below "
            "and never make up new ones. Users may ask in natural language, including requests for recipes, "
            "ingredient preferences, allergies, dietary restrictions, available ingredients, or general guidance. "
            "Interpret their intent and provide the best matching recipe(s) from the list. "
            "Always format your response in clear Markdown with these sections: "
            "- Name\n- Rating\n- Preparation Time\n- Ingredients (bullet list)\n- Steps (numbered list)\n- Description\n- Nutrition (if available)\n\n"
            "Be polite, concise, and helpful. Do not invent recipes or ingredients.\n\n"
            f"Available recipes:\n{database_context}"
        )

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            max_tokens=700
        )

        answer = response.choices[0].message.content
        return JsonResponse({"answer": answer})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

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

    common_ingredients = [
        "Olive oil", "Garlic", "Onion", "Butter", "Chicken",
        "Pasta", "Tomato", "Eggs", "Flour", "Sugar"
    ]

    # Merge sets
    all_ingredients.update(common_ingredients)

    # Sort ingredients: common ones first, then the rest alphabetically
    sorted_ingredients = common_ingredients + sorted(all_ingredients - set(common_ingredients))


    # Paginate — show 10 recipes per page
    paginator = Paginator(all_recipes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'all_ingredients': sorted_ingredients,
    }

    return render(request, 'home/index.html', context)

def feeling_lucky(request):
    recipe_ids = list(Recipe.objects.values_list("recipe_id", flat=True))

    if not recipe_ids:
        messages.error(request, "No recipes available.")
        return redirect("home:index")

    random_id = random.choice(recipe_ids)
    return redirect("home:recipe", recipe_id=random_id)

def recipe(request, recipe_id):
    recipe = get_object_or_404(Recipe, recipe_id=recipe_id)
    interactions = Interaction.objects.filter(recipe=recipe).order_by('-date')

    user_review = None
    if request.user.is_authenticated:
        user_review = Interaction.objects.filter(
            recipe=recipe,
            user_id=request.user.id
        ).first()

    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect("home:login")

        if user_review:
            messages.error(request, "You have already submitted a review.")
        else:
            form = ReviewForm(request.POST)
            if form.is_valid():
                new_review = form.save(commit=False)
                new_review.user_id = request.user.id
                new_review.date = date.today()
                new_review.recipe = recipe
                new_review.save()
                return redirect("home:recipe", recipe_id=recipe_id)
    else:
        form = ReviewForm()
    
    if request.method == "POST" and "delete" in request.POST:
        if request.user.is_authenticated and (request.user.is_superuser or request.user.id == recipe.contributor_id):
            recipe.delete()
            return redirect("home:index")
        else:
            messages.error(request, "You are not allowed to delete this recipe.")

    is_favorited = False
    if request.user.is_authenticated:
        is_favorited = Favorite.objects.filter(user=request.user, recipe=recipe).exists()

    return render(request, 'home/recipe.html', {
        'recipe': recipe,
        'ingredients': recipe.get_ingredients(),
        'steps': recipe.get_steps(),
        'tags': recipe.get_tags(),
        'nutrition': recipe.get_nutrition(),
        'interactions': interactions,
        'form': form,
        'user_review': user_review,
        'is_favorited': is_favorited,
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

@require_GET
def filter_recipes_by_ingredient(request):
    ingredients = request.GET.getlist("ingredient")
    page_number = int(request.GET.get("page", 1))
    per_page = 10

    if not ingredients:
        return JsonResponse({"error": "No ingredients provided"}, status=400)

    # Query all recipes in DB
    all_recipes = Recipe.objects.all()

    # Filter recipes containing all selected ingredients (AND logic)
    filtered_recipes = []
    for recipe in all_recipes:  # <-- iterates over entire database
        recipe_ings = [ing.lower() for ing in recipe.get_ingredients()]
        if all(any(sel_ing.lower() in ing for ing in recipe_ings) for sel_ing in ingredients):
            filtered_recipes.append(recipe)

    # Annotate ratings
    for r in filtered_recipes:
        r.avg_rating = r.interactions.aggregate(avg=Avg("rating"))["avg"] or 0
        r.review_count = r.interactions.count()

    # Paginate filtered recipes
    total = len(filtered_recipes)
    num_pages = (total + per_page - 1) // per_page
    start = (page_number - 1) * per_page
    end = start + per_page
    page_recipes = filtered_recipes[start:end]

    recipes_list = [
        {
            "name": r.name,
            "recipe_id": r.recipe_id,
            "avg_rating": round(r.avg_rating, 2),
            "review_count": r.review_count,
        }
        for r in page_recipes
    ]

    pagination = {
        "current": page_number,
        "num_pages": num_pages,
        "has_previous": page_number > 1,
        "has_next": page_number < num_pages,
        "page_range": list(range(1, num_pages + 1)),
    }

    return JsonResponse({"recipes": recipes_list, "pagination": pagination})


@login_required
def toggle_favorite(request, recipe_id):
    recipe = get_object_or_404(Recipe, recipe_id=recipe_id)
    favorite, created = Favorite.objects.get_or_create(user=request.user, recipe=recipe)

    if not created:
        favorite.delete()   # it was already a favorite → unfavorite

    return redirect("home:recipe", recipe_id=recipe_id)

@login_required
def add_recipe(request):
    if request.method == "POST":
        # Auto-generate a 10-digit recipe_id
        recipe_id = ''.join([str(random.randint(0, 9)) for _ in range(10)])

        # Convert input fields to JSON format
        tags_input = request.POST.get("tags", "")  # e.g., easy, dinner
        tags_json = json.dumps([t.strip() for t in tags_input.split(",") if t.strip()])

        steps_input = request.POST.get("steps", "")  # e.g., Mix ingredients, Bake for 20 minutes
        steps_json = json.dumps([s.strip() for s in steps_input.split(",") if s.strip()])

        ingredients_input = request.POST.get("ingredients", "")  # e.g., flour, eggs, milk
        ingredients_json = json.dumps([i.strip() for i in ingredients_input.split(",") if i.strip()])

        nutrition_input = request.POST.get("nutrition", "")  # e.g., 100,5,10,50,20,8
        nutrition_json = json.dumps([int(n) for n in nutrition_input.replace(",", " ").split() if n.strip()])

        Recipe.objects.create(
            name=request.POST.get("name", ""),
            recipe_id=recipe_id,
            minutes=int(request.POST.get("minutes", 0)),
            contributor_id=request.user.id,
            submitted=date.today(),
            description=request.POST.get("description", ""),
            tags=tags_json,
            nutrition=nutrition_json,
            n_steps=int(request.POST.get("n_steps", 0)),
            steps=steps_json,
            ingredients=ingredients_json,
            n_ingredients=int(request.POST.get("n_ingredients", 0)),
        )

        return redirect("home:index")

    return render(request, "home/add_recipe.html")

@login_required
def edit_recipe(request, recipe_id):
    recipe = get_object_or_404(Recipe, recipe_id=recipe_id)

    # Only allow owner or admin
    if not (request.user.is_superuser or request.user.id == recipe.contributor_id):
        return redirect('home:index')

    if request.method == "POST":
        if "edit" in request.POST:
            recipe.name = request.POST.get("name", recipe.name)
            recipe.minutes = int(request.POST.get("minutes", recipe.minutes))
            recipe.description = request.POST.get("description", recipe.description)

            # Tags
            tags_input = request.POST.get("tags", "")
            try:
                # If already JSON, keep it
                recipe.tags = json.dumps(json.loads(tags_input))
            except json.JSONDecodeError:
                # Otherwise, split by comma
                recipe.tags = json.dumps([t.strip() for t in tags_input.split(",")])

            # Steps
            steps_input = request.POST.get("steps", "")
            try:
                recipe.steps = json.dumps(json.loads(steps_input))
            except json.JSONDecodeError:
                recipe.steps = json.dumps([s.strip() for s in steps_input.split(";")])

            # Ingredients
            ingredients_input = request.POST.get("ingredients", "")
            try:
                recipe.ingredients = json.dumps(json.loads(ingredients_input))
            except json.JSONDecodeError:
                recipe.ingredients = json.dumps([i.strip() for i in ingredients_input.split(",")])

            # Nutrition
            nutrition_input = request.POST.get("nutrition", "")
            try:
                recipe.nutrition = json.dumps(json.loads(nutrition_input))
            except json.JSONDecodeError:
                recipe.nutrition = json.dumps([float(n.strip()) for n in nutrition_input.split(",")])

            recipe.n_steps = int(request.POST.get("n_steps", recipe.n_steps))
            recipe.n_ingredients = int(request.POST.get("n_ingredients", recipe.n_ingredients))

            recipe.save()
            return redirect('home:recipe', recipe_id=recipe.recipe_id)

        elif "delete" in request.POST:
            recipe.delete()
            return redirect('home:index')

    return render(request, "home/edit_recipe.html", {"recipe": recipe})

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

@login_required
def my_recipes(request):
    # Recipes the user created
    created_recipes = Recipe.objects.filter(contributor_id=request.user.id)

    # Recipes the user favorited
    favorite_recipes = Recipe.objects.filter(favorite__user=request.user)

    return render(request, "home/my_recipes.html", {
        "recipes": created_recipes,
        "favorites": favorite_recipes,
    })