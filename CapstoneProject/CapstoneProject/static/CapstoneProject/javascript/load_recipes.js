document.addEventListener("DOMContentLoaded", function () {
  const recipeList = document.getElementById("recipe-list");

  // Fetch recipe data via AJAX
  fetch("/load_recipes/")
    .then((response) => response.json())
    .then((data) => {
      recipeList.innerHTML = ""; // Clear existing
      data.recipes.forEach((recipe) => {
        const li = document.createElement("li");
        li.innerHTML = `
          <a href="/recipe/${recipe.id}/">
            ${recipe.name}
          </a>
          <br><small>⭐ ${recipe.rating} (${recipe.review_count} reviews)</small>
        `;
        recipeList.appendChild(li);
      });
    })
    .catch((error) => {
      recipeList.innerHTML = "<li>Error loading recipes</li>";
      console.error("Error fetching recipes:", error);
    });
});