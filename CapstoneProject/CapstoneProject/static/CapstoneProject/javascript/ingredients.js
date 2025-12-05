document.addEventListener("DOMContentLoaded", () => {
    const ingredientItems = Array.from(document.querySelectorAll(".ingredient-item"));
    const searchBox = document.getElementById("ingredient-search");
    const searchBtn = document.getElementById("ingredient-search-btn");
    const showMoreBtn = document.getElementById("show-more-btn");
    const showLessBtn = document.getElementById("show-less-btn");
    const clearSelectionBtn = document.getElementById("clear-selection-btn");

    let visibleCount = 20;
    const increment = 20;

    const renderList = () => {
        ingredientItems.forEach((item, index) => {
            item.style.display = index < visibleCount ? "" : "none";
        });
        if (showMoreBtn) showMoreBtn.style.display = visibleCount < ingredientItems.length ? "inline-block" : "none";
        if (showLessBtn) showLessBtn.style.display = visibleCount > 20 ? "inline-block" : "none";
    };

    const filterIngredients = () => {
        const term = searchBox.value.toLowerCase().trim();

        if (!term) {
            visibleCount = 20;
            renderList();
            return;
        }

        ingredientItems.forEach(item => {
            const btn = item.querySelector(".ingredient-btn");
            if (!btn) return;
            const name = btn.dataset.ingredient.toLowerCase();
            item.style.display = name.includes(term) ? "" : "none";
        });

        // Hide Show More / Less while searching
        if (showMoreBtn) showMoreBtn.style.display = "none";
        if (showLessBtn) showLessBtn.style.display = "none";
    };

    // Search box input triggers live filter (optional)
    if (searchBox) {
        searchBox.addEventListener("input", filterIngredients);
        searchBox.addEventListener("keypress", e => {
            if (e.key === "Enter") {
                e.preventDefault();
                filterIngredients();
            }
        });
    }

    // Search button triggers filter
    if (searchBtn) {
        searchBtn.addEventListener("click", e => {
            e.preventDefault();
            filterIngredients();
        });
    }

    // Show more / less buttons
    if (showMoreBtn) showMoreBtn.addEventListener("click", () => {
        visibleCount += increment;
        renderList();
    });

    if (showLessBtn) showLessBtn.addEventListener("click", () => {
        visibleCount = 20;
        renderList();
    });

    // Clear selection
    if (clearSelectionBtn) clearSelectionBtn.addEventListener("click", () => {
        ingredientItems.forEach(item => {
            const btn = item.querySelector(".ingredient-btn");
            if (!btn) return;
            btn.classList.remove("btn-success");
            btn.classList.add("btn-outline-secondary");
        });
    });

    // Toggle selection on ingredient buttons
    ingredientItems.forEach(item => {
        const btn = item.querySelector(".ingredient-btn");
        if (!btn) return;
        btn.addEventListener("click", () => {
            btn.classList.toggle("btn-success");
            btn.classList.toggle("btn-outline-secondary");
        });
    });

    renderList();
});
