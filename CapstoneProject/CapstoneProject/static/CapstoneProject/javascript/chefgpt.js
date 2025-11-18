$(document).on("submit", "#chefgpt-form", function(e) {
    e.preventDefault();

    let question = $("#chefgpt-input").val();
    let csrfToken = $("input[name=csrfmiddlewaretoken]").val();

    $("#chefgpt-response").html("<p class='text-info'>Thinking...</p>");

    $.ajax({
        url: "/chefgpt/",
        type: "POST",
        data: {
            "question": question,
            "csrfmiddlewaretoken": csrfToken
        },
        success: function(data) {
            $("#chefgpt-response").html("<p>" + data.answer + "</p>");
        },
        error: function(xhr) {
            let errorMsg = "An error occurred.";
            if (xhr.responseJSON && xhr.responseJSON.error) {
                errorMsg = xhr.responseJSON.error;
            }
            $("#chefgpt-response").html("<p class='text-danger'>Error: " + errorMsg + "</p>");
        }
    });
});