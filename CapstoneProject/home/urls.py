from django.urls import path
from home import views

app_name = 'home'

urlpatterns = [
    path('', views.home, name='index'),
    path('recipe/<int:recipe_id>/', views.recipe, name='recipe'),
    path("add_recipe/", views.add_recipe, name="add_recipe"),
    path('chefgpt/', views.chefgpt, name='chefgpt'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('logout/', views.logout_view, name='logout'),
    path('load_recipes/', views.load_recipes, name='load_recipes'),  # AJAX route
    path("filter_recipes/", views.filter_recipes_by_ingredient, name="filter_recipes"),
]