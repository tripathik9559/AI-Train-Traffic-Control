/**
 * Railway Control System — Main JavaScript
 * Global utilities: sidebar, theme, toast, counters, AJAX helpers
 */

'use strict';

// ─── Theme Management ─────────────────────────────────
const Theme = {
  STORAGE_KEY: 'rcs-theme',
  current: 'dark',

  init() {
    const saved = localStorage.getItem(this.STORAGE_KEY) || 'dark';
    this.apply(saved);
  },

  apply(theme) {
    this.current = theme;
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(this.STORAGE_KEY, theme);

    // Update toggle button icon
    const btn = document.getElementById('theme-toggle');
    if (btn) {
      btn.innerHTML = theme === 'dark'
        ? '<i class="bi bi-sun-fill" style="font-size:1rem;color:#f59e0b;"></i>'
        : '<i class="bi bi-moon-fill" style="font-size:1rem;color:#6366f1;"></i>';
      btn.setAttribute('title', theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode');
    }

    // Update Chart.js global defaults if available
    if (typeof Chart !== 'undefined') {
      const textColor    = theme === 'dark' ? '#8892a4' : '#475569';
      const gridColor    = theme === 'dark' ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.07)';
      const tooltipBg    = theme === 'dark' ? '#1a2234' : '#ffffff';
      const tooltipColor = theme === 'dark' ? '#e8eaf0' : '#1e293b';
      Chart.defaults.color              = textColor;
      Chart.defaults.plugins.tooltip.backgroundColor = tooltipBg;
      Chart.defaults.plugins.tooltip.titleColor      = tooltipColor;
      Chart.defaults.plugins.tooltip.bodyColor       = tooltipColor;
      Chart.defaults.plugins.tooltip.borderColor     = theme === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)';
      Chart.defaults.plugins.tooltip.borderWidth     = 1;
      if (Chart.defaults.scale) {
        Chart.defaults.scale.grid.color         = gridColor;
        Chart.defaults.scale.ticks.color        = textColor;
      }
    }

    // Dispatch event so individual pages can react (e.g. re-draw D3 networks)
    document.dispatchEvent(new CustomEvent('themechange', { detail: { theme } }));
  },

  toggle() {
    this.apply(this.current === 'dark' ? 'light' : 'dark');
  }
};

// ─── Sidebar Management ───────────────────────────────
const Sidebar = {
  STORAGE_KEY: 'rcs-sidebar',

  init() {
    const sidebar = document.querySelector('.sidebar');
    const wrapper = document.querySelector('.main-wrapper');
    const saved = localStorage.getItem(this.STORAGE_KEY);
    if (saved === 'collapsed' && sidebar && wrapper) {
      sidebar.classList.add('collapsed');
      wrapper.classList.add('sidebar-collapsed');
    }
  },

  toggle() {
    const sidebar = document.querySelector('.sidebar');
    const wrapper = document.querySelector('.main-wrapper');
    if (!sidebar || !wrapper) return;
    const isCollapsed = sidebar.classList.toggle('collapsed');
    wrapper.classList.toggle('sidebar-collapsed', isCollapsed);
    localStorage.setItem(this.STORAGE_KEY, isCollapsed ? 'collapsed' : 'expanded');
  },

  mobileOpen() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    sidebar?.classList.add('mobile-open');
    overlay?.classList.add('active');
  },

  mobileClose() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    sidebar?.classList.remove('mobile-open');
    overlay?.classList.remove('active');
  }
};

// ─── Toast Notifications ──────────────────────────────
const Toast = {
  container: null,

  init() {
    this.container = document.getElementById('toast-container');
    if (!this.container) {
      this.container = document.createElement('div');
      this.container.id = 'toast-container';
      this.container.className = 'toast-container';
      document.body.appendChild(this.container);
    }
  },

  show(message, type = 'info', duration = 4000) {
    if (!this.container) this.init();

    const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
      <span style="font-size:1.1rem">${icons[type] || icons.info}</span>
      <div style="flex:1">
        <div style="font-size:0.875rem;font-weight:600;color:var(--text-primary)">${message}</div>
      </div>
      <button onclick="this.parentElement.remove()" style="background:none;border:none;color:var(--text-muted);cursor:pointer;font-size:1rem">×</button>
    `;
    this.container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      toast.style.transition = '0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, duration);
  },

  success: (msg, d) => Toast.show(msg, 'success', d),
  error: (msg, d) => Toast.show(msg, 'error', d),
  warning: (msg, d) => Toast.show(msg, 'warning', d),
  info: (msg, d) => Toast.show(msg, 'info', d),
};

// ─── Animated Counter ─────────────────────────────────
function animateCounter(el, start, end, duration = 1000, suffix = '') {
  if (!el) return;
  const range = end - start;
  const startTime = performance.now();

  function update(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    const value = Math.round(start + range * eased);
    el.textContent = value.toLocaleString() + suffix;
    if (progress < 1) requestAnimationFrame(update);
  }
  requestAnimationFrame(update);
}

function initCounters() {
  document.querySelectorAll('[data-counter]').forEach(el => {
    const target = parseFloat(el.dataset.counter) || 0;
    const suffix = el.dataset.suffix || '';
    const duration = parseInt(el.dataset.duration) || 1200;
    animateCounter(el, 0, target, duration, suffix);
  });
}

// ─── CSRF Helper ──────────────────────────────────────
function getCsrfToken() {
  return document.cookie.split(';')
    .find(c => c.trim().startsWith('csrftoken='))
    ?.split('=')[1] || '';
}

// ─── AJAX Helper ──────────────────────────────────────
async function apiPost(url, data = {}) {
  const resp = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCsrfToken(),
    },
    body: JSON.stringify(data),
  });
  return resp.json();
}

async function apiGet(url) {
  const resp = await fetch(url, {
    headers: { 'X-Requested-With': 'XMLHttpRequest' }
  });
  return resp.json();
}

// ─── Real-time clock ──────────────────────────────────
function initClock() {
  const el = document.getElementById('current-time');
  if (!el) return;
  const update = () => {
    const now = new Date();
    el.textContent = now.toLocaleTimeString('en-IN', {
      hour: '2-digit', minute: '2-digit', second: '2-digit',
      hour12: false
    });
  };
  update();
  setInterval(update, 1000);
}

// ─── Notification count refresh ───────────────────────
async function refreshNotifCount() {
  try {
    const data = await apiGet('/api/notifications/unread-count/');
    const badge = document.getElementById('notif-count');
    if (badge) {
      badge.textContent = data.count || '';
      badge.style.display = data.count > 0 ? 'flex' : 'none';
    }
  } catch (e) { /* silently fail */ }
}

// ─── Loading screen ───────────────────────────────────
function hideLoadingScreen() {
  const ls = document.getElementById('loading-screen');
  if (ls) {
    ls.style.opacity = '0';
    setTimeout(() => ls.remove(), 500);
  }
}

// ─── Confirm dialog helper ────────────────────────────
function confirmAction(message, callback) {
  if (window.confirm(message)) callback();
}

// ─── Form validation ──────────────────────────────────
function validateForm(formEl) {
  let valid = true;
  formEl.querySelectorAll('[required]').forEach(input => {
    const parent = input.closest('.form-group') || input.parentElement;
    const errEl = parent.querySelector('.invalid-feedback') || document.createElement('div');
    if (!input.value.trim()) {
      input.classList.add('is-invalid');
      errEl.className = 'invalid-feedback';
      errEl.textContent = 'This field is required.';
      if (!parent.querySelector('.invalid-feedback')) parent.appendChild(errEl);
      valid = false;
    } else {
      input.classList.remove('is-invalid');
      const existing = parent.querySelector('.invalid-feedback');
      if (existing) existing.remove();
    }
  });
  return valid;
}

// ─── Search debounce ──────────────────────────────────
function debounce(fn, delay = 300) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

// ─── Live search setup ────────────────────────────────
function initLiveSearch(inputId, url, tableBodyId) {
  const input = document.getElementById(inputId);
  if (!input) return;

  const handler = debounce(async () => {
    const q = input.value.trim();
    if (q.length < 2 && q.length !== 0) return;
    const data = await apiGet(`${url}?search=${encodeURIComponent(q)}`);
    // Applications handle their own rendering
    document.dispatchEvent(new CustomEvent('search-results', { detail: data }));
  });

  input.addEventListener('input', handler);
}

// ─── Conflict detection trigger ───────────────────────
async function runConflictDetection() {
  const btn = document.getElementById('detect-conflicts-btn');
  if (btn) { btn.disabled = true; btn.textContent = '⏳ Detecting...'; }

  try {
    const data = await apiPost('/api/conflicts/detect/');
    if (data.success) {
      Toast.success(`${data.detected} conflict(s) detected for today.`);
      setTimeout(() => location.reload(), 2000);
    } else {
      Toast.error('Detection failed. Try again.');
    }
  } catch (e) {
    Toast.error('Network error during detection.');
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = '🔍 Run Detection'; }
  }
}

// ─── Status update helper ─────────────────────────────
async function updateTrainStatus(trainId, status, delay) {
  const data = await apiPost(`/api/trains/${trainId}/status/`, { status, delay });
  if (data.success) {
    Toast.success(`Train status updated: ${status}`);
    return true;
  } else {
    Toast.error('Failed to update train status.');
    return false;
  }
}

// ─── Section status update ────────────────────────────
async function updateSectionStatus(sectionId, status) {
  const data = await apiPost(`/api/stations/sections/${sectionId}/status/`, { status });
  if (data.success) {
    Toast.success(`Section status updated: ${status}`);
    return data;
  } else {
    Toast.error('Failed to update section status.');
    return null;
  }
}

// ─── Django messages auto-hide ────────────────────────
function initMessages() {
  document.querySelectorAll('.django-message').forEach(el => {
    const type = el.dataset.type || 'info';
    Toast.show(el.textContent.trim(), type);
    el.remove();
  });
}

// ─── Dropdown menus ───────────────────────────────────
function initDropdowns() {
  document.querySelectorAll('[data-dropdown]').forEach(trigger => {
    trigger.addEventListener('click', (e) => {
      e.stopPropagation();
      const targetId = trigger.dataset.dropdown;
      const menu = document.getElementById(targetId);
      if (menu) {
        menu.style.display = menu.style.display === 'block' ? 'none' : 'block';
      }
    });
  });

  document.addEventListener('click', () => {
    document.querySelectorAll('.dropdown-menu').forEach(m => m.style.display = 'none');
  });
}

// ─── Intersection Observer for animations ─────────────
function initScrollAnimations() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('slide-up');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.animate-on-scroll').forEach(el => observer.observe(el));
}

// ─── Main Init ────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  Theme.init();
  Sidebar.init();
  Toast.init();
  initCounters();
  initClock();
  initMessages();
  initDropdowns();
  initScrollAnimations();

  hideLoadingScreen();

  // Notification refresh every 30s
  refreshNotifCount();
  setInterval(refreshNotifCount, 30000);

  // Sidebar toggle button
  document.getElementById('sidebar-toggle')?.addEventListener('click', Sidebar.toggle.bind(Sidebar));
  document.getElementById('sidebar-mobile-toggle')?.addEventListener('click', Sidebar.mobileOpen.bind(Sidebar));
  document.getElementById('sidebar-overlay')?.addEventListener('click', Sidebar.mobileClose.bind(Sidebar));

  // Theme toggle
  document.getElementById('theme-toggle')?.addEventListener('click', Theme.toggle.bind(Theme));

  // Conflict detection
  document.getElementById('detect-conflicts-btn')?.addEventListener('click', runConflictDetection);

  // Django messages hidden spans
  document.querySelectorAll('.message-data').forEach(el => {
    Toast.show(el.dataset.message, el.dataset.type || 'info');
    el.remove();
  });
});
