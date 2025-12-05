document.addEventListener("DOMContentLoaded", function () {
    const ingredientButtons = document.querySelectorAll(".ingredient-btn");
    const recipeAccordion = document.getElementById("recipeAccordion");

    ingredientButtons.forEach(button => {
        button.addEventListener("click", () => {
            const ingredient = button.dataset.ingredient;

            // Highlight selected ingredient
            ingredientButtons.forEach(b => b.classList.remove("btn-success"));
            button.classList.add("btn-success");

            // Fetch filtered recipes from Django
            fetch("/filter_recipes/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCSRFToken(),
                },
                body: JSON.stringify({ ingredient: ingredient }),
            })
            .then(response => response.json())
            .then(data => {
                if (data.recipes) {
                    updateRecipeList(data.recipes);
                } else {
                    recipeAccordion.innerHTML = `<p class="text-muted">No recipes found for "${ingredient}".</p>`;
                }
            })
            .catch(err => console.error("Error:", err));
        });
    });

    function getCSRFToken() {
        const name = "csrftoken=";
        const decoded = decodeURIComponent(document.cookie);
        const cookies = decoded.split(";");
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name)) {
                return cookie.substring(name.length);
            }
        }
        return "";
    }

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
});