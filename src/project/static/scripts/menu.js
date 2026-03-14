function openMenu() {
    document.getElementById("menu").classList.remove("hidden");
    document.getElementById("menu-button").setAttribute("aria-expanded", "true");
}

function closeMenu() {
    document.getElementById("menu").classList.add("hidden");
    document.getElementById("menu-button").setAttribute("aria-expanded", "false");
}
