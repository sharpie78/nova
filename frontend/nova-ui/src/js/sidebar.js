document.addEventListener("DOMContentLoaded", () => {
  const sidebar = document.querySelector('.sidebar');

  // === Inject toggle button ===
  const toggleBtn = document.createElement('div');
  toggleBtn.classList.add('toggle-btn');
  toggleBtn.innerHTML = `<span class="material-symbols-outlined">menu</span>`;
  sidebar.insertBefore(toggleBtn, sidebar.firstChild);

  // === Toggle collapse/expand ===
  toggleBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    sidebar.classList.toggle('collapsed');
  });

  // === Collapse on outside click ===
  document.addEventListener('click', (e) => {
    if (!sidebar.contains(e.target)) {
      sidebar.classList.add('collapsed');
    }
  });

  // === Make entire <li> clickable, not just <a> ===
  sidebar.querySelectorAll('li').forEach(li => {
    li.addEventListener('click', () => {
      const link = li.querySelector('a');
      if (link) window.location.href = link.href;
    });
  });
});

// ✅ Logout helper
function logoutUser() {
  localStorage.removeItem("jwtToken");
  window.location.href = "login.html";
}
