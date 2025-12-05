document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".step-checkbox").forEach(cb => {
        cb.addEventListener("change", () => {
            const container = cb.closest(".list-group-item");
            const text = container.querySelector(".step-text");
            text.classList.toggle("step-done", cb.checked);
        });
    });
});