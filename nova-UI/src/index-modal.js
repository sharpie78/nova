// Sidebar toggle functionality
function toggleSidebar() {
  document.querySelector('.sidebar').classList.toggle('collapsed');
}

// Modal functionality
const modal = document.getElementById('modal');
const modalTitle = document.getElementById('modal-title');
const modalBody = document.getElementById('modal-body');
const modalClose = modal.querySelector('.modal-close');
let socket = null;  // Declare socket globally
let lastOpenedCard = null; // Track last opened card

// Open modal function
function openModal(title, content, icon) {
  // Close WebSocket if the modal being opened is not "System"
  if (socket && title !== 'System') {
    closeWebSocket();
  }

  // Check if the same card is clicked twice (toggle functionality)
  if (lastOpenedCard === title) {
    closeModal();
    return;
  }

  lastOpenedCard = title;

  // Special handling for AI Model Management
  if (title === 'AI Model Management') {
    fetch('model-modal.html')
      .then(res => res.text())
      .then(html => {
        modalTitle.innerText = icon + ' ' + title;
        modalBody.innerHTML = html;
        modal.classList.remove('hidden');

        const script = document.createElement('script');
        script.src = 'model-modal.js';
        script.onload = () => refreshModels();
        document.body.appendChild(script);
      });
    return;
  }

  // Update the modal title, body, and show modal
  modalTitle.innerText = icon + ' ' + title;
  modalBody.innerHTML = content;
  modal.classList.remove('hidden');

  if (title === 'System Status') {
    const notificationsContent = ``;

    modalBody.innerHTML = notificationsContent;

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

// Close modal function
function closeModal() {
  modal.classList.add('hidden');
  closeWebSocket();
  lastOpenedCard = null;
}

// Close WebSocket when switching modals or navigating
function closeWebSocket() {
  if (socket) {
    socket.close();
    socket = null;
  }
}

// Handle click for dashboard cards
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

// Close modal when the close button is clicked
modalClose.addEventListener('click', closeModal);

// Helper functions to determine dot color based on value
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

document.addEventListener("DOMContentLoaded", function() {
    const socket = new WebSocket("ws://localhost:56969/ws/system-info");

    // Fetch system info once and close the socket immediately after receiving data
    socket.onopen = function() {
        console.log("WebSocket connected for system info.");
    };

    socket.onmessage = function(event) {
        const systemInfo = JSON.parse(event.data);  // Parse and use the received data

        // Update the system card with fetched data
        updateSystemCard(systemInfo);

        // Close the WebSocket after receiving the data
        socket.close();
        console.log("WebSocket closed after receiving system info.");
    };

    socket.onerror = function(error) {
        console.error("WebSocket Error: ", error);
    };

    // Handle card click to display the same info again (if needed)
    document.querySelector(".dashboard-card").addEventListener("click", function() {
        updateSystemCard(systemInfo);
    });
});
function updateSystemCard(systemInfo) {
  const systemInfoElement = document.getElementById("system-info");

  if (systemInfoElement && systemInfo) {
    let formattedInfo = '';

    // Display each system info section with color-coded headings
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

    systemInfoElement.innerHTML = formattedInfo;  // Update the system info in the card
  }
}
