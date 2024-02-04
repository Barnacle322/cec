// Get all forms in the document
const forms = document.querySelectorAll("form");

forms.forEach((form) => {
    const submitButton = form.querySelector("button[type='submit']");

    form.addEventListener("submit", function (event) {
        submitButton.disabled = true;
        submitButton.innerText = "Загрузка...";
        submitButton.classList.add("cursor-not-allowed");
    });
});
