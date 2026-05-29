(() => {
  const cfg = window.DASHBOARD || {};
  const S = cfg.strings || {};
  const order = cfg.order || [];
  const refreshSeconds = cfg.refreshSeconds || 20;

  const $ = (sel) => document.querySelector(sel);
  const segmentsEl = $("#segments");
  const onlineEl = $("#online-count");
  const totalEl = $("#total-count");
  const subtitleEl = $("#subtitle");
  const countdownEl = $("#countdown");
  const vpnBadge = $("#vpn-badge");

  // Build the segmented health bar once, in config order.
  const segByKey = {};
  order.forEach((key) => {
    const seg = document.createElement("span");
    seg.className = "seg";
    segmentsEl.appendChild(seg);
    segByKey[key] = seg;
  });

  function pad(n) { return String(n).padStart(2, "0"); }

  function tickClock() {
    const d = new Date();
    $("#clock").textContent = `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
  }

  function applyCard(key, info) {
    const card = document.querySelector(`.card[data-key="${key}"]`);
    if (!card) return;
    const statusEl = card.querySelector(".card-status");
    const latencyEl = card.querySelector(".latency");
    statusEl.dataset.state = info.state;
    if (info.state === "up") {
      latencyEl.textContent = `${info.ms} ms`;
    } else if (info.state === "down") {
      latencyEl.textContent = S.offline_state || "offline";
    } else {
      latencyEl.textContent = S.disabled_state || "disabled";
    }
  }

  function applySummary(services) {
    let online = 0, offline = 0, disabled = 0;
    order.forEach((key) => {
      const st = services[key] && services[key].state;
      const seg = segByKey[key];
      if (seg) seg.className = `seg ${st || ""}`;
      if (st === "up") online++;
      else if (st === "down") offline++;
      else if (st === "disabled") disabled++;
    });
    const enabled = online + offline;
    onlineEl.textContent = online;
    totalEl.textContent = enabled;

    const parts = [];
    if (offline > 0) parts.push(`<span class="off-count">${offline} ${S.offline_state || "offline"}</span>`);
    if (disabled > 0) parts.push(`<span>${disabled} ${S.disabled_state || "disabled"}</span>`);
    subtitleEl.innerHTML = parts.join(" · ");
  }

  function applyVpn(on) {
    if (!vpnBadge) return;
    vpnBadge.classList.toggle("is-on", !!on);
    vpnBadge.classList.toggle("is-off", !on);
    vpnBadge.querySelector(".label").textContent = on ? (S.vpn_on || "VPN active") : (S.vpn_off || "VPN inactive");
  }

  async function refresh() {
    try {
      const res = await fetch("api/status.php", { cache: "no-store" });
      const data = await res.json();
      Object.entries(data.services).forEach(([key, info]) => applyCard(key, info));
      applySummary(data.services);
      applyVpn(data.vpn);
    } catch (e) {
      // Leave the last known state on transient failures.
    }
  }

  let remaining = refreshSeconds;
  function tickCountdown() {
    countdownEl.textContent = remaining;
    if (remaining <= 0) {
      remaining = refreshSeconds;
      refresh();
    }
    remaining--;
  }

  $("#refresh").addEventListener("click", () => {
    remaining = refreshSeconds;
    refresh();
  });

  tickClock();
  refresh();
  setInterval(tickClock, 1000);
  setInterval(tickCountdown, 1000);
})();
