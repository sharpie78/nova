// Modal functionality
const modal = document.getElementById('modal');
const modalTitle = document.getElementById('modal-title');
const modalBody = document.getElementById('modal-body');
const modalClose = modal.querySelector('.modal-close');
let socket = null;  // Declare socket globally
let lastOpenedCard = null; // Track last opened card
let systemInfo = null; // FIX: make systemInfo accessible globally

// Open modal function
function openModal(title, content, icon) {
  if (socket && title !== 'System') {
    closeWebSocket();
  }

  if (lastOpenedCard === title) {
    closeModal();
    return;
  }

  lastOpenedCard = title;

  if (title === 'AI Model Management') {
    fetch('../html/model-modal.html')
      .then(res => res.text())
      .then(html => {
        modalTitle.innerText = icon + ' ' + title;
        modalBody.innerHTML = html;
        modal.classList.remove('hidden');

        const script = document.createElement('script');
        script.src = '../js/model-modal.js';
        script.onload = () => refreshModels();
        document.body.appendChild(script);
      });
    return;
  }

  modalTitle.innerText = icon + ' ' + title;
  modalBody.innerHTML = content;
  modal.classList.remove('hidden');

  if (title === 'System Status') {
    modalBody.innerHTML = ``;

    if (socket) socket.close();

    socket = new WebSocket('ws://localhost:56969/ws/system-status');

    socket.onopen = () => console.log('WebSocket connection established');

    socket.onmessage = (event) => {
      const stats = JSON.parse(event.data);
      const systemStatusContent = `
        <ul>
          <li><span class="dot ${getCpuUsageDotClass(stats.cpu_usage)}">●</span>CPU Usage: ${stats.cpu_usage}%</li>
          <li><span class="dot ${getCpuTempDotClass(stats.cpu_temp)}">●</span>CPU Temp: ${stats.cpu_temp}°C</li>
          <li><span class="dot ${getRamDotClass(stats.ram_used_gb, stats.ram_total_gb)}">●</span>RAM: ${stats.ram_used_gb} / ${stats.ram_total_gb} GiB</li>
          <li><span class="dot ${getGpuTempDotClass(stats.gpus[0].temperature)}">●</span>GPU 1 Temp: ${stats.gpus[0].temperature}°C</li>
          <li><span class="dot ${getGpuLoadDotClass(stats.gpus[0].utilization)}">●</span>GPU 1 Load: ${stats.gpus[0].utilization}%</li>
          <li><span class="dot ${getGpuMemDotClass(stats.gpus[0].mem_used, stats.gpus[0].mem_total)}">●</span>GPU 1 Mem: ${(stats.gpus[0].mem_used / 1024).toFixed(2)} / ${(stats.gpus[0].mem_total / 1024).toFixed(2)} GB</li>
          <li><span class="dot ${getGpuTempDotClass(stats.gpus[1].temperature)}">●</span>GPU 2 Temp: ${stats.gpus[1].temperature}°C</li>
          <li><span class="dot ${getGpuLoadDotClass(stats.gpus[1].utilization)}">●</span>GPU 2 Load: ${stats.gpus[1].utilization}%</li>
          <li><span class="dot ${getGpuMemDotClass(stats.gpus[1].mem_used, stats.gpus[1].mem_total)}">●</span>GPU 2 Mem: ${(stats.gpus[1].mem_used / 1024).toFixed(2)} / ${(stats.gpus[1].mem_total / 1024).toFixed(2)} GB</li>
        </ul>
      `;

      const section = document.querySelector('.system-status');
      if (section) section.innerHTML = systemStatusContent;
      else {
        const newSection = document.createElement('div');
        newSection.classList.add('modal-section', 'system-status');
        newSection.innerHTML = systemStatusContent;
        modalBody.appendChild(newSection);
      }
    };

    socket.onerror = (error) => console.error('WebSocket error:', error);

    socket.onclose = (event) => {
      console.log('WebSocket closed');
      if (!event.wasClean) {
        console.log('Reconnecting...');
        setTimeout(() => {
          socket = new WebSocket('ws://localhost:56969/ws/system-status');
        }, 5000);
      }
    };
  }
}

function closeModal() {
  modal.classList.add('hidden');
  closeWebSocket();
  lastOpenedCard = null;
}

function closeWebSocket() {
  if (socket) {
    socket.close();
    socket = null;
  }
}

document.querySelectorAll('.dashboard-card').forEach(card => {
  card.style.cursor = 'pointer';
  card.addEventListener('click', () => {
    const title = card.getAttribute('data-modal-title');
    const h3Text = card.querySelector('h3').innerText;
    const emojiMatch = h3Text.match(/^[^\w\s]+/);
    const icon = emojiMatch ? emojiMatch[0] : '';
    const content = card.getAttribute('data-modal-content');

    openModal(title, content, icon);
  });
});

modalClose.addEventListener('click', closeModal);

// Helpers
function getCpuUsageDotClass(cpuUsage) {
  if (cpuUsage < 50) return 'green';
  if (cpuUsage < 80) return 'yellow';
  return 'red';
}

function getCpuTempDotClass(cpuTemp) {
  if (cpuTemp < 60) return 'green';
  if (cpuTemp < 75) return 'yellow';
  return 'red';
}

function getRamDotClass(ramUsedGb, ramTotalGb) {
  const percent = (ramUsedGb / ramTotalGb) * 100;
  if (percent < 50) return 'green';
  if (percent < 80) return 'yellow';
  return 'red';
}

function getGpuTempDotClass(temp) {
  if (temp < 55) return 'green';
  if (temp < 75) return 'yellow';
  return 'red';
}

function getGpuLoadDotClass(load) {
  if (load < 50) return 'green';
  if (load < 80) return 'yellow';
  return 'red';
}

function getGpuMemDotClass(used, total) {
  const percent = (used / total) * 100;
  if (percent < 50) return 'green';
  if (percent < 80) return 'yellow';
  return 'red';
}

document.addEventListener("DOMContentLoaded", function () {
  const socket = new WebSocket("ws://localhost:56969/ws/system-info");

  socket.onopen = function () {
    console.log("WebSocket connected for system info.");
  };

  socket.onmessage = function (event) {
    systemInfo = JSON.parse(event.data); // FIX: save to outer variable
    updateSystemCard(systemInfo);
    socket.close();
    console.log("WebSocket closed after receiving system info.");
  };

  socket.onerror = function (error) {
    console.error("WebSocket Error: ", error);
  };

  document.querySelector(".dashboard-card").addEventListener("click", function () {
    updateSystemCard(systemInfo);
  });
});

function updateSystemCard(systemInfo) {
  const systemInfoElement = document.getElementById("system-info");

  if (systemInfoElement && systemInfo) {
    let formattedInfo = '';

    if (systemInfo.OS) {
      formattedInfo += `<p><span class="system-info-heading os">OS:</span> ${systemInfo.OS}</p>`;
    }
    if (systemInfo.Uptime) {
      formattedInfo += `<p><span class="system-info-heading uptime">Uptime:</span> ${systemInfo.Uptime}</p>`;
    }
    if (systemInfo.Kernel) {
      formattedInfo += `<p><span class="system-info-heading kernel">Kernel:</span> ${systemInfo.Kernel}</p>`;
    }
    if (systemInfo.Shell) {
      formattedInfo += `<p><span class="system-info-heading shell">Shell:</span> ${systemInfo.Shell}</p>`;
    }
    if (systemInfo.CPU) {
      formattedInfo += `<p><span class="system-info-heading cpu">CPU:</span> ${systemInfo.CPU}</p>`;
    }
    if (systemInfo.GPU) {
      formattedInfo += `<p><span class="system-info-heading gpu">GPU:</span> ${systemInfo.GPU}</p>`;
    }
    if (systemInfo.Memory) {
      formattedInfo += `<p><span class="system-info-heading ram">Memory:</span> ${systemInfo.Memory}</p>`;
    }

    systemInfoElement.innerHTML = formattedInfo;
  }
}
