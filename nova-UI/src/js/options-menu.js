document.addEventListener("DOMContentLoaded", () => {
  const moreBtn = document.querySelector(".options-toggle");
  if (!moreBtn) return;

  const dropdown = document.createElement("ul");
  dropdown.className = "options-menu";
  dropdown.style.display = "none";

  const item = document.createElement("li");
  item.textContent = "Logout";
  item.addEventListener("click", () => {
    localStorage.removeItem("jwtToken");
    window.location.href = "login.html";
  });

  dropdown.appendChild(item);
  document.body.appendChild(dropdown);

  moreBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    dropdown.style.display = dropdown.style.display === "none" ? "block" : "none";
  });

  document.addEventListener("click", (e) => {
    if (!dropdown.contains(e.target)) {
      dropdown.style.display = "none";
    }
  });
});
