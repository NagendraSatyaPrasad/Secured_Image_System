document.addEventListener("DOMContentLoaded", () => {
  const themeToggle = document.getElementById("darkModeToggle");
  const body = document.getElementById("pageBody");

  if (!themeToggle || !body) return;

  // Load saved theme
  if (localStorage.getItem("theme") === "dark") {
    body.classList.add("dark-mode");
    themeToggle.textContent = "☀️ Light Mode";
    themeToggle.classList.remove("bg-white", "text-black");
    themeToggle.classList.add("bg-gray-800", "text-white");
  }

  // Toggle theme on click
  themeToggle.addEventListener("click", () => {
    body.classList.toggle("dark-mode");

    if (body.classList.contains("dark-mode")) {
      localStorage.setItem("theme", "dark");
      themeToggle.textContent = "☀️ Light Mode";
      themeToggle.classList.remove("bg-white", "text-black");
      themeToggle.classList.add("bg-gray-800", "text-white");
    } else {
      localStorage.setItem("theme", "light");
      themeToggle.textContent = "🌙 Dark Mode";
      themeToggle.classList.remove("bg-gray-800", "text-white");
      themeToggle.classList.add("bg-white", "text-black");
    }
  });
});







