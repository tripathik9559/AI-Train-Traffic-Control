/**
 * Railway Control System — Simulator Utilities
 * Shared logic for the real-time operations simulator.
 */

'use strict';

/* ─── Train position interpolator ─────────────────────── */
class TrainAnimator {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.trains = new Map(); // id → { el, x, y, targetX, targetY }
  }

  update(trainStates) {
    if (!this.container) return;

    trainStates.forEach(t => {
      if (!this.trains.has(t.id)) {
        this._createMarker(t);
      }
      this._updateMarker(t);
    });

    // Remove stale markers
    for (const [id] of this.trains) {
      if (!trainStates.find(t => t.id === id)) {
        const info = this.trains.get(id);
        info.el.remove();
        this.trains.delete(id);
      }
    }
  }

  _createMarker(t) {
    const el = document.createElement('div');
    el.className = 'train-marker';
    el.id = `marker-${t.id}`;
    el.title = `${t.number} — ${t.name}`;
    el.style.cssText = `
      position:absolute;
      width:28px; height:18px;
      background:${t.type_color || '#3b82f6'};
      border-radius:4px;
      display:flex; align-items:center; justify-content:center;
      font-size:0.6rem; font-weight:800; color:white;
      font-family:var(--font-mono);
      cursor:pointer;
      box-shadow:0 2px 8px rgba(0,0,0,0.4);
      transition:left 0.6s linear, top 0.6s linear;
      z-index:10;
      border:1px solid rgba(255,255,255,0.3);
    `;
    el.textContent = t.number.slice(-4);
    el.addEventListener('click', () => this._showTrainPopup(t));
    this.container.appendChild(el);

    const pos = this._calcPosition(t);
    el.style.left = pos.x + 'px';
    el.style.top  = pos.y + 'px';

    this.trains.set(t.id, { el, ...pos, data: t });
  }

  _updateMarker(t) {
    const info = this.trains.get(t.id);
    if (!info) return;

    const pos = this._calcPosition(t);
    info.el.style.left = pos.x + 'px';
    info.el.style.top  = pos.y + 'px';
    info.el.style.background = t.delay > 10 ? '#f59e0b' : (t.type_color || '#3b82f6');
    info.el.title = `${t.number} | ${t.status} | +${t.delay}' | ${t.speed} km/h`;

    // Pulse on conflict
    if (t.delay > 30) {
      info.el.style.animation = 'statusPulse 1s infinite';
    } else {
      info.el.style.animation = '';
    }

    this.trains.get(t.id).data = t;
  }

  _calcPosition(t) {
    // Map progress (0–100) to x-axis; priority affects y spread
    const containerW = (this.container.offsetWidth  || 800) - 40;
    const containerH = (this.container.offsetHeight || 400) - 30;
    const x = (t.progress / 100) * containerW;
    const y = ((t.priority - 1) / 4) * (containerH - 40) + 10 + (t.id % 20) * 4;
    return { x: Math.max(0, Math.min(x, containerW)), y: Math.max(0, Math.min(y, containerH)) };
  }

  _showTrainPopup(t) {
    if (typeof Toast !== 'undefined') {
      Toast.info(
        `🚂 ${t.number} — ${t.status} | Speed: ${t.speed} km/h | Delay: +${t.delay}'`,
        3000
      );
    }
  }

  clear() {
    this.trains.forEach(info => info.el.remove());
    this.trains.clear();
  }
}

/* ─── Section status renderer ──────────────────────────── */
function renderSectionGrid(containerId, sections) {
  const container = document.getElementById(containerId);
  if (!container) return;

  container.innerHTML = '';
  sections.forEach(s => {
    const div = document.createElement('div');
    div.style.cssText = `
      background:${s.color}18;
      border:1px solid ${s.color}55;
      border-radius:8px;
      padding:8px 12px;
      min-width:110px;
      cursor:default;
      transition:all 0.3s ease;
    `;
    div.innerHTML = `
      <div style="font-family:var(--font-mono);font-size:0.72rem;font-weight:700;color:${s.color};">
        ${s.from}—${s.to}
      </div>
      <div style="font-size:0.65rem;color:var(--text-muted);margin-top:2px;">${s.status}</div>
    `;
    container.appendChild(div);
  });
}

/* ─── Event log writer ─────────────────────────────────── */
class EventLogger {
  constructor(logId, maxLines = 80) {
    this.el = document.getElementById(logId);
    this.maxLines = maxLines;
    this.colors = {
      info:    '#8892a4',
      success: '#10b981',
      warning: '#f59e0b',
      error:   '#ef4444',
      system:  '#3b82f6',
    };
  }

  log(msg, type = 'info') {
    if (!this.el) return;
    const now = new Date().toLocaleTimeString('en-IN', { hour12: false });
    const div = document.createElement('div');
    div.style.color = this.colors[type] || this.colors.info;
    div.textContent = `[${now}] ${msg}`;
    this.el.appendChild(div);
    this.el.scrollTop = this.el.scrollHeight;

    while (this.el.children.length > this.maxLines) {
      this.el.removeChild(this.el.firstChild);
    }
  }

  clear() {
    if (this.el) this.el.innerHTML = '';
  }
}

/* ─── Conflict flash overlay ───────────────────────────── */
function flashConflict(message, duration = 3000) {
  const overlay = document.createElement('div');
  overlay.style.cssText = `
    position:fixed; top:80px; left:50%; transform:translateX(-50%);
    background:rgba(239,68,68,0.95);
    color:white;
    padding:14px 24px;
    border-radius:12px;
    font-size:0.9rem;
    font-weight:700;
    z-index:8000;
    display:flex;
    align-items:center;
    gap:10px;
    box-shadow:0 4px 24px rgba(239,68,68,0.5);
    animation:slideUp 0.3s ease;
  `;
  overlay.innerHTML = `<span style="font-size:1.2rem;">⚠️</span> ${message}`;
  document.body.appendChild(overlay);
  setTimeout(() => {
    overlay.style.opacity = '0';
    overlay.style.transition = '0.3s';
    setTimeout(() => overlay.remove(), 300);
  }, duration);
}

/* ─── Export ───────────────────────────────────────────── */
window.RCS = window.RCS || {};
Object.assign(window.RCS, {
  TrainAnimator,
  EventLogger,
  renderSectionGrid,
  flashConflict,
});
