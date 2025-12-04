document.addEventListener("DOMContentLoaded", function () {
    const FILTER_RECIPES_URL = "/filter_recipes_by_ingredient/";
    const ingredientButtons = document.querySelectorAll(".ingredient-btn");
    const recipeAccordion = document.getElementById("recipeAccordion");
    const clearButton = document.getElementById("clear-selection-btn");
    const paginationContainer = document.querySelector(".pagination");

    let selectedIngredients = [];

    // --- Load recipes for selected ingredients and page ---
    function loadRecipes(page = 1) {
        if (selectedIngredients.length === 0) {
            // No ingredients selected, show normal recipes
            location.href = "/";
            return;
        }

        const params = new URLSearchParams();
        selectedIngredients.forEach(ing => params.append("ingredient", ing));
        params.append("page", page);

        fetch(`${FILTER_RECIPES_URL}?${params.toString()}`)
            .then(response => response.json())
            .then(data => {
                if (!data.recipes || data.recipes.length === 0) {
                    recipeAccordion.innerHTML = `<p class="text-muted">No recipes found for this selection.</p>`;
                    paginationContainer.innerHTML = "";
                    return;
                }

                updateRecipeList(data.recipes);
                renderPagination(data.pagination);
            })
            .catch(err => console.error("Error:", err));
    }

    // --- Update accordion with recipes ---
    function updateRecipeList(recipes) {
        recipeAccordion.innerHTML = "";
        recipes.forEach((r, i) => {
            const html = `
                <div class="accordion-item">
                    <h2 class="accordion-header" id="heading${i}">
                        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse"
                            data-bs-target="#collapse${i}" aria-expanded="false" aria-controls="collapse${i}">
                            <strong>${r.name}</strong> — ⭐ ${r.avg_rating || "N/A"} (${r.review_count} reviews)
                        </button>
                    </h2>
                    <div id="collapse${i}" class="accordion-collapse collapse"
                        aria-labelledby="heading${i}" data-bs-parent="#recipeAccordion">
                        <div class="accordion-body">
                            <a href="/recipe/${r.recipe_id}/" class="btn btn-primary btn-sm mt-2">View Full Recipe</a>
                        </div>
                    </div>
                </div>`;
            recipeAccordion.insertAdjacentHTML("beforeend", html);
        });
    }

    // --- Render pagination for filtered recipes ---
    function renderPagination(pagination) {
        if (!paginationContainer) return;
        paginationContainer.innerHTML = "";

        const current = pagination.current;
        const numPages = pagination.num_pages;

        // Show up to 2 pages before and after current
        const start = Math.max(1, current - 2);
        const end = Math.min(numPages, current + 2);

        if (current > 1) {
            paginationContainer.insertAdjacentHTML(
                "beforeend",
                `<li class="page-item"><a class="page-link" href="#" data-page="${current - 1}">Previous</a></li>`
            );
        }

        for (let i = start; i <= end; i++) {
            const activeClass = i === current ? "active" : "";
            paginationContainer.insertAdjacentHTML(
                "beforeend",
                `<li class="page-item ${activeClass}"><a class="page-link" href="#" data-page="${i}">${i}</a></li>`
            );
        }

        if (current < numPages) {
            paginationContainer.insertAdjacentHTML(
                "beforeend",
                `<li class="page-item"><a class="page-link" href="#" data-page="${current + 1}">Next</a></li>`
            );
        }
    }

    // --- Ingredient button click ---
    ingredientButtons.forEach(button => {
        button.addEventListener("click", () => {
            const ing = button.dataset.ingredient;

            if (selectedIngredients.includes(ing)) {
                selectedIngredients = selectedIngredients.filter(i => i !== ing);
                button.classList.remove("btn-success");
                button.classList.add("btn-outline-secondary");
            } else {
                selectedIngredients.push(ing);
                button.classList.remove("btn-outline-secondary");
                button.classList.add("btn-success");
            }

            loadRecipes(1); // Always start at page 1
        });
    });

    // --- Pagination button click ---
    document.addEventListener("click", function (e) {
        if (e.target.classList.contains("page-link")) {
            if (selectedIngredients.length === 0) return; // Normal pagination works
            e.preventDefault();
            const page = parseInt(e.target.dataset.page);
            if (!isNaN(page)) loadRecipes(page);
        }
    });

    // --- Clear selection button ---
    if (clearButton) {
        clearButton.addEventListener("click", () => {
            selectedIngredients = [];
            ingredientButtons.forEach(b => {
                b.classList.remove("btn-success");
                b.classList.add("btn-outline-secondary");
            });
            location.href = "/";
        });
    }
});
