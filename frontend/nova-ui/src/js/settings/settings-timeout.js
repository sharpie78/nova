// settings-timeout.js
(() => {
  const API = "http://127.0.0.1:56969";
  const LOGIN_PATH = "../../html/login.html";
  const TOKEN_KEY = "jwtToken";
  const SETTINGS_POLL_MS = 10000; // re-check settings every 10s so changes apply while logged in
  const WARNING_SECONDS = 30;

  const username = localStorage.getItem("username");
  if (!username) return;

  // ---- x-tab comms
  const bc = ("BroadcastChannel" in window) ? new BroadcastChannel("nova-activity") : null;
  const bcSend = (type, data = {}) => {
    if (bc) return bc.postMessage({ type, ...data, ts: Date.now() });
    // storage fallback broadcast
    localStorage.setItem("nova:activity:event", JSON.stringify({ type, ...data, ts: Date.now() }));
    // cleanup key to keep storage tidy (still triggers the event)
    setTimeout(() => localStorage.removeItem("nova:activity:event"), 0);
  };
  const onBroadcast = (fn) => {
    if (bc) bc.onmessage = (e) => fn(e.data);
    window.addEventListener("storage", (e) => {
      if (e.key === "nova:activity:event" && e.newValue) {
        try { fn(JSON.parse(e.newValue)); } catch {}
      }
      if (e.key === "nova:activity-timeout-ms" && e.newValue) {
        const ms = parseInt(e.newValue, 10);
        if (!Number.isNaN(ms)) rearm(ms);
      }
    });
  };

  // ---- map label → minutes
  const labelToMinutes = (label) => {
    if (!label) return 30;
    const l = String(label).trim().toLowerCase();
    if (l === "never") return 0;
    const n = parseInt(l, 10);
    return Number.isFinite(n) ? n : 30;
  };

  // ---- state
  let idleMs = 0;
  let idleTimer = null;
  let warningTimer = null;
  let countdownTimer = null;
  let countdownLeft = WARNING_SECONDS;
  let lastAppliedMs = -1;

  // ---- UI banner
  let banner;
  const ensureBanner = () => {
    if (banner) return banner;
    banner = document.createElement("div");
    banner.style.cssText = [
    "position:fixed","top:50%","left:50%","transform:translate(-50%,-50%)",
    "padding:24px 28px","background:#111","color:#fff",
    "font:20px/1.4 system-ui, -apple-system, Segoe UI, Roboto, sans-serif",
    "border-radius:16px","box-shadow:0 12px 36px rgba(0,0,0,.35)",
    "z-index:2147483647","display:none","text-align:center",
    "max-width:560px","width:max-content","pointer-events:none"
    ].join(";");
    banner.innerHTML = `
    <span id="nova-activity-msg" style="display:block;">
        You’ll be logged out in
        <b id="nova-activity-count" style="font-size:1.4em;">${WARNING_SECONDS}</b>s.
        <br/>Move the mouse or press a key to stay logged in.
    </span>`;
    document.body.appendChild(banner);
    return banner;
  };
  const showBanner = () => { ensureBanner().style.display = "flex"; };
  const hideBanner = () => { if (banner) banner.style.display = "none"; };

  // ---- timers
  const clearAll = () => {
    if (idleTimer) clearTimeout(idleTimer), idleTimer = null;
    if (warningTimer) clearTimeout(warningTimer), warningTimer = null;
    if (countdownTimer) clearInterval(countdownTimer), countdownTimer = null;
    hideBanner();
  };

  const scheduleIdle = () => {
    if (idleMs <= 0) return; // "never"
    if (!localStorage.getItem(TOKEN_KEY)) return; // no session
    idleTimer = setTimeout(onIdleReached, idleMs);
  };

  const onIdleReached = () => {
    // start warning window
    countdownLeft = WARNING_SECONDS;
    updateCountdown(countdownLeft);
    showBanner();
    // every second
    countdownTimer = setInterval(() => {
      countdownLeft -= 1;
      updateCountdown(Math.max(countdownLeft, 0));
      if (countdownLeft <= 0) {
        clearInterval(countdownTimer); countdownTimer = null;
        doLogoutAllTabs();
      }
    }, 1000);
    // also set a safety timeout
    warningTimer = setTimeout(() => {
      if (countdownTimer) { clearInterval(countdownTimer); countdownTimer = null; }
      doLogoutAllTabs();
    }, WARNING_SECONDS * 1000 + 100); // tiny buffer
  };

  const updateCountdown = (v) => {
    const el = document.getElementById("nova-activity-count");
    if (el) el.textContent = String(v);
  };

  // ---- activity handlers (mouse/keyboard/touch/scroll ONLY)
  const activityEvents = ["mousemove","mousedown","keydown","touchstart","scroll"];
  const onActivity = () => {
    if (!localStorage.getItem(TOKEN_KEY)) return; // already logged out
    // if warning visible, hide it and cancel countdown
    if (banner && banner.style.display !== "none") {
      hideBanner();
      if (warningTimer) clearTimeout(warningTimer), warningTimer = null;
      if (countdownTimer) clearInterval(countdownTimer), countdownTimer = null;
    }
    // reset main idle timer
    if (idleTimer) clearTimeout(idleTimer);
    scheduleIdle();

    // broadcast to other tabs
    bcSend("activity");
  };

  activityEvents.forEach(ev => window.addEventListener(ev, onActivity, true));

  // ---- x-tab listeners
  onBroadcast((msg) => {
    if (!msg || !msg.type) return;
    if (msg.type === "activity") {
      // mirror reset from another tab
      if (banner && banner.style.display !== "none") {
        hideBanner();
        if (warningTimer) clearTimeout(warningTimer), warningTimer = null;
        if (countdownTimer) clearInterval(countdownTimer), countdownTimer = null;
      }
      if (idleTimer) clearTimeout(idleTimer);
      scheduleIdle();
    }
    if (msg.type === "logout") {
      doLogoutLocal();
    }
  });

  const doLogoutAllTabs = () => {
    bcSend("logout");
    doLogoutLocal();
  };

  const doLogoutLocal = () => {
    clearAll();
    localStorage.removeItem(TOKEN_KEY);
    // hard redirect
    window.location.replace(LOGIN_PATH);
  };

  // ---- settings
  const fetchActivityTimeoutMs = async () => {
    try {
      const r = await fetch(`${API}/settings/${username}`);
      if (!r.ok) return null;
      const s = await r.json();
      const label = s?.interface?.["Activity timeout"]?.default;
      const mins = labelToMinutes(label);
      return mins <= 0 ? 0 : mins * 60 * 1000;
    } catch {
      return null;
    }
  };

  const rearm = (ms) => {
    if (typeof ms !== "number") return;
    if (ms === lastAppliedMs) return; // no change
    lastAppliedMs = ms;
    idleMs = ms;
    clearAll();
    if (idleMs > 0) scheduleIdle();
  };

  // periodic re-fetch so setting changes take effect while logged in
  const startSettingsWatcher = () => {
    let stopping = false;
    const tick = async () => {
      if (stopping) return;
      const ms = await fetchActivityTimeoutMs();
      if (ms !== null) rearm(ms);
      setTimeout(tick, SETTINGS_POLL_MS);
    };
    tick();
    // also react when tab becomes visible again
    document.addEventListener("visibilitychange", async () => {
      if (!document.hidden) {
        const ms = await fetchActivityTimeoutMs();
        if (ms !== null) rearm(ms);
      }
    });
  };

  // bootstrap
  (async () => {
    const ms = await fetchActivityTimeoutMs();
    if (ms === null) return;    // couldn't load settings; bail quietly
    rearm(ms);                  // arm initial timer
    startSettingsWatcher();     // keep it fresh while logged in
  })();
})();
