document.addEventListener("DOMContentLoaded", function () {
    var elements = document.querySelectorAll(".element");
    var currentIndex = 0;

    function toggleElements() {
        elements.forEach(function (element, index) {
            if (index === currentIndex) {
                element.classList.remove("opacity-0");
                element.classList.add("opacity-100");
            } else {
                element.classList.remove("opacity-100");
                element.classList.add("opacity-0");
            }
        });

        currentIndex = (currentIndex + 1) % elements.length;
    }

    setInterval(toggleElements, 4000); // Change the interval (in milliseconds) as needed
});
