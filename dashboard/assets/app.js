(() => {
  const cfg = window.DASHBOARD || {};
  const S = cfg.strings || {};
  const names = cfg.names || {};
  const refreshSeconds = cfg.refreshSeconds || 20;
  const historySize = cfg.historySize || 12;

  const $ = (sel) => document.querySelector(sel);
  const fmt = (tpl, vars) => (tpl || "").replace(/\{(\w+)\}/g, (_, k) => vars[k] ?? "");

  const headlineEl = $("#headline");
  const subtitleEl = $("#subtitle");
  const alertEl = $("#alert-line");
  const liveDot = $("#live-dot");
  const countdownEl = $("#countdown");
  const progressEl = $("#progress-bar");
  const refreshIcon = $("#refresh-icon");
  const vpnBadge = $("#vpn-badge");

  // Last `historySize` probes per service (null ms = failed), kept in memory
  // only: a reload starts a fresh sparkline. `failStreak` counts consecutive
  // failures for the alert line.
  const history = {};
  const failStreak = {};

  function pad(n) { return String(n).padStart(2, "0"); }

  function tickClock() {
    const d = new Date();
    $("#clock").textContent = `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
  }

  function record(key, info) {
    const h = (history[key] = history[key] || []);
    h.push(info.state === "up" ? info.ms : null);
    if (h.length > historySize) h.shift();
    failStreak[key] = info.state === "down" ? (failStreak[key] || 0) + 1 : 0;
  }

  function drawSpark(row, key) {
    const spark = row.querySelector(".spark");
    if (!spark) return;
    const h = history[key] || [];
    const max = Math.max(1, ...h.filter((v) => v !== null));
    const bars = spark.children;
    // Right-align the samples so the newest probe is always the last bar.
    const offset = bars.length - h.length;
    for (let i = 0; i < bars.length; i++) {
      const bar = bars[i];
      const v = h[i - offset];
      if (i < offset) {
        bar.className = "";
        bar.style.height = "";
      } else if (v === null) {
        bar.className = "fail";
        bar.style.height = "";
      } else {
        bar.className = i === bars.length - 1 ? "ok last" : "ok";
        bar.style.height = `${Math.max(2, Math.round((v / max) * 16))}px`;
      }
    }
  }

  function applyRow(key, info) {
    const row = document.querySelector(`.row[data-key="${key}"]`);
    if (!row) return;
    row.dataset.state = info.state;
    const status = row.querySelector(".status");
    if (info.state === "up") status.textContent = `${info.ms} ms`;
    else if (info.state === "down") status.textContent = S.offline || "Offline";
    else status.textContent = S.disabled || "Disabled";
    drawSpark(row, key);
  }

  function applyPanels(services) {
    document.querySelectorAll(".panel").forEach((panel) => {
      let up = 0, on = 0;
      panel.querySelectorAll(".row").forEach((row) => {
        const st = services[row.dataset.key] && services[row.dataset.key].state;
        if (st === "up" || st === "down") on++;
        if (st === "up") up++;
      });
      panel.querySelector(".panel-count").textContent = `${up}/${on}`;
    });
  }

  function applySummary(services) {
    const up = [], down = [], disabled = [], latencies = [];
    Object.entries(services).forEach(([key, info]) => {
      if (info.state === "up") { up.push(key); latencies.push(info.ms); }
      else if (info.state === "down") down.push(key);
      else disabled.push(key);
    });

    document.querySelectorAll("#strip span").forEach((seg) => {
      const st = services[seg.dataset.key] && services[seg.dataset.key].state;
      seg.className = st === "up" || st === "down" ? st : "";
    });

    headlineEl.textContent = down.length === 0 ? S.all_online
      : down.length === 1 ? S.one_down
      : fmt(S.many_down, { n: down.length });

    const parts = [fmt(S.up_of_total, { up: up.length, total: up.length + down.length })];
    if (disabled.length) parts.push(`${disabled.map((k) => names[k] || k).join(", ")} ${S.disabled_state}`);
    if (latencies.length) {
      const sorted = latencies.slice().sort((a, b) => a - b);
      parts.push(fmt(S.median, { ms: sorted[Math.floor(sorted.length / 2)] }));
    }
    subtitleEl.textContent = parts.join(" · ");

    if (down.length) {
      const streak = Math.min(...down.map((k) => failStreak[k] || 1));
      const reason = streak > 1 ? fmt(S.no_response_n, { n: streak }) : S.no_response_1;
      alertEl.textContent = `${down.map((k) => names[k] || k).join(", ")} — ${reason}`;
      alertEl.hidden = false;
    } else {
      alertEl.hidden = true;
    }

    liveDot.className = `live-dot ${down.length ? "is-alert" : "is-ok"}`;
  }

  function applyVpn(on) {
    if (!vpnBadge) return;
    vpnBadge.classList.toggle("is-alert", !on);
    vpnBadge.querySelector(".label").textContent = on ? S.vpn_on : S.vpn_off;
  }

  async function refresh() {
    try {
      const res = await fetch("api/status.php", { cache: "no-store" });
      const data = await res.json();
      Object.entries(data.services).forEach(([key, info]) => {
        if (info.state !== "disabled") record(key, info);
        applyRow(key, info);
      });
      applyPanels(data.services);
      applySummary(data.services);
      applyVpn(data.vpn);
    } catch (e) {
      // Leave the last known state on transient failures.
    }
  }

  let remaining = refreshSeconds;
  function drawCountdown() {
    countdownEl.textContent = remaining;
    // Snap back to full without animating; drain linearly otherwise.
    const full = remaining === refreshSeconds;
    progressEl.style.transition = full ? "none" : "width 1s linear";
    progressEl.style.width = `${(remaining / refreshSeconds) * 100}%`;
  }

  function tickCountdown() {
    remaining--;
    if (remaining <= 0) {
      remaining = refreshSeconds;
      refresh();
    }
    drawCountdown();
  }

  let angle = 0;
  $("#refresh").addEventListener("click", () => {
    angle += 360;
    refreshIcon.style.transform = `rotate(${angle}deg)`;
    remaining = refreshSeconds;
    drawCountdown();
    refresh();
  });

  tickClock();
  drawCountdown();
  refresh();
  setInterval(tickClock, 1000);
  setInterval(tickCountdown, 1000);
})();
