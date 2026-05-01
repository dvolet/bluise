// 🌙 DARK MODE TOGGLE
const toggleBtn = document.querySelector(".dark-toggle");

if (toggleBtn) {
    toggleBtn.addEventListener("click", () => {
        document.body.classList.toggle("dark-mode");

        // Save preference
        if (document.body.classList.contains("dark-mode")) {
            localStorage.setItem("theme", "dark");
        } else {
            localStorage.setItem("theme", "light");
        }
    });
}

// LOAD SAVED THEME
if (localStorage.getItem("theme") === "dark") {
    document.body.classList.add("dark-mode");
}

// 🍔 HAMBURGER MENU
const menuToggle = document.querySelector(".menu-toggle");
const navLinks = document.querySelector(".nav-links");

if (menuToggle) {
    menuToggle.addEventListener("click", () => {
        navLinks.classList.toggle("show");
    });
}

// 👁 PASSWORD TOGGLE
const eyes = document.querySelectorAll(".eye");

eyes.forEach(eye => {
    eye.addEventListener("click", () => {
        const input = eye.previousElementSibling;

        if (input.type === "password") {
            input.type = "text";
            eye.textContent = "🙈";
        } else {
            input.type = "password";
            eye.textContent = "👁";
        }
    });
});
