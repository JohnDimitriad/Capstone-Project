document.addEventListener("DOMContentLoaded", () => {
    // Ingredient list elements
    const ingredientItems = Array.from(document.querySelectorAll(".ingredient-item"));
    const searchBox = document.getElementById("ingredient-search");
    const searchBtn = document.getElementById("ingredient-search-btn");
    const showMoreBtn = document.getElementById("show-more-btn");
    const showLessBtn = document.getElementById("show-less-btn");
    const clearSelectionBtn = document.getElementById("clear-selection-btn");

    // Recipe elements
    const recipeCards = document.querySelectorAll(".accordion-item");
    const ingredientButtons = document.querySelectorAll(".ingredient-btn");

    // Config
    const increment = 10;
    let visibleCount = increment;
    let currentItems = [];

    // Selected ingredients for recipe filtering
    let selectedIngredients = [];

    // RECIPE FILTERING
    const filterRecipes = () => {
        if (selectedIngredients.length === 0) {
            recipeCards.forEach(card => card.style.display = "");
            return;
        }

        recipeCards.forEach(card => {
            const recipeIngredients = card.dataset.ingredients.toLowerCase();

            const matchesAll = selectedIngredients.every(ing =>
                recipeIngredients.includes(ing)
            );

            card.style.display = matchesAll ? "" : "none";
        });
    };

    // INGREDIENT BUTTON TOGGLE
    ingredientButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            btn.classList.toggle("btn-success");
            btn.classList.toggle("btn-outline-secondary");

            const ing = btn.dataset.ingredient.toLowerCase();

            if (btn.classList.contains("btn-success")) {
                if (!selectedIngredients.includes(ing)) {
                    selectedIngredients.push(ing);
                }
            } else {
                selectedIngredients = selectedIngredients.filter(i => i !== ing);
            }

            filterRecipes();
        });
    });

    const renderInitial = () => {
        currentItems = ingredientItems; 
        ingredientItems.forEach(item => item.style.display = "none");
        visibleCount = Math.min(increment, currentItems.length);
        currentItems.slice(0, visibleCount).forEach(item => item.style.display = "");

        showMoreBtn.style.display = visibleCount < currentItems.length ? "inline-block" : "none";
        showLessBtn.style.display = "none";
    };

    const renderList = () => {
        currentItems.forEach((item, index) => {
            item.style.display = index < visibleCount ? "" : "none";
        });

        showMoreBtn.style.display = visibleCount < currentItems.length ? "inline-block" : "none";
        showLessBtn.style.display = visibleCount > increment ? "inline-block" : "none";
    };

    const filterIngredients = () => {
        const term = searchBox.value.toLowerCase().trim();

        if (!term) {
            visibleCount = increment;
            renderInitial();
            return;
        }

        currentItems = ingredientItems.filter(item => {
            const btn = item.querySelector(".ingredient-btn");
            return btn && btn.dataset.ingredient.toLowerCase().includes(term);
        });

        visibleCount = Math.min(increment, currentItems.length);
        ingredientItems.forEach(item => item.style.display = "none");
        renderList();
    };

    // SEARCH EVENTS
    if (searchBtn) {
        searchBtn.type = "button";
        searchBtn.addEventListener("click", filterIngredients);
    }

    if (searchBox) {
        searchBox.addEventListener("keypress", e => {
            if (e.key === "Enter") {
                e.preventDefault();
                filterIngredients();
            }
        });
    }

    // SHOW MORE / LESS
    if (showMoreBtn) showMoreBtn.addEventListener("click", () => {
        visibleCount = Math.min(visibleCount + increment, currentItems.length);
        renderList();
    });

    if (showLessBtn) showLessBtn.addEventListener("click", () => {
        visibleCount = increment;
        renderList();
    });

    // CLEAR SELECTION (global reset)
    if (clearSelectionBtn) clearSelectionBtn.addEventListener("click", () => {

        // reset ingredient buttons UI
        ingredientButtons.forEach(btn => {
            btn.classList.remove("btn-success");
            btn.classList.add("btn-outline-secondary");
        });

        selectedIngredients = [];
        filterRecipes();

        // reset ingredient list view
        if (searchBox) searchBox.value = "";
        renderInitial();
    });

    renderInitial();
});
