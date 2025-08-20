document.addEventListener("DOMContentLoaded", () => {
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
