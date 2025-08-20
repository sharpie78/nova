const appWindow = window.__TAURI__.window.getCurrentWindow();

document.getElementById('titlebar-minimize')?.addEventListener('click', () => {
  appWindow.minimize();
});
document.getElementById('titlebar-maximize')?.addEventListener('click', () => {
  appWindow.toggleMaximize();
});
document.getElementById('titlebar-close')?.addEventListener('click', () => {
  appWindow.close();
});


function toggleMainMenu() {
  const menu = document.getElementById("main-menu");
  menu.classList.toggle("hidden");
  document.addEventListener("click", function hide(e) {
    if (!menu.contains(e.target) && !e.target.closest("#menu-toggle")) {
      menu.classList.add("hidden");
      document.removeEventListener("click", hide);
    }
  });
}

function updateStopButtonVisibility() {
  const speakActive = document.getElementById('speak-button')?.classList.contains('active');
  const listenActive = document.getElementById('listen-button')?.classList.contains('active');
  const stop = document.getElementById('stop-button');
  if (speakActive || listenActive) {
    stop.classList.remove('hidden');
  } else {
    stop.classList.add('hidden');
  }
}

