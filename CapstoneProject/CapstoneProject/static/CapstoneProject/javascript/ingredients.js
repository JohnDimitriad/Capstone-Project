document.addEventListener("DOMContentLoaded", function () {
  const ingredientItems = document.querySelectorAll(".ingredient-item");
  const ingredientButtons = document.querySelectorAll(".ingredient-btn");
  const showMoreBtn = document.getElementById("show-more-btn");
  const showLessBtn = document.getElementById("show-less-btn");

  let visibleCount = 10;

  function updateVisibility() {
    ingredientItems.forEach((item, index) => {
      item.style.display = index < visibleCount ? "block" : "none";
    });

    showMoreBtn.style.display = visibleCount < ingredientItems.length ? "inline-block" : "none";
    showLessBtn.style.display = visibleCount > 10 ? "inline-block" : "none";
  }

  // Initial show
  updateVisibility();

  showMoreBtn.addEventListener("click", () => {
    visibleCount += 10;
    updateVisibility();
  });

  showLessBtn.addEventListener("click", () => {
    visibleCount = 10;
    updateVisibility();
    window.scrollTo({ top: 0, behavior: "smooth" });
  });

  // ✅ Ingredient selection logic
  const selectedIngredients = new Set();

  ingredientButtons.forEach(button => {
    button.addEventListener("click", () => {
      const ingredient = button.dataset.ingredient;

      if (selectedIngredients.has(ingredient)) {
        selectedIngredients.delete(ingredient);
        button.classList.remove("btn-success");
        button.classList.add("btn-outline-secondary");
      } else {
        selectedIngredients.add(ingredient);
        button.classList.add("btn-success");
        button.classList.remove("btn-outline-secondary");
      }

      filterRecipes();
    });
  });

  function filterRecipes() {
    const recipes = document.querySelectorAll(".accordion-item");

    recipes.forEach(recipe => {
      const ingredientsText = recipe.dataset.ingredients?.toLowerCase() || "";
      const matches = [...selectedIngredients].every(ing => ingredientsText.includes(ing.toLowerCase()));

      recipe.style.display = matches || selectedIngredients.size === 0 ? "" : "none";
    });
  }
});

document.addEventListener("DOMContentLoaded", function () {
  const searchBox = document.querySelector('input[placeholder="Search for an Ingredient"]');
  const ingredientButtons = document.querySelectorAll(".ingredient-item");

  searchBox.addEventListener("input", function () {
    const query = this.value.toLowerCase().trim();

    ingredientButtons.forEach((item) => {
      const ingredient = item.textContent.toLowerCase();
      if (ingredient.includes(query)) {
        item.style.display = "block";
      } else {
        item.style.display = "none";
      }
    });
  });
});