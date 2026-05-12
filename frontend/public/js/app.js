/** LexChain Sovereign - Main Application Module */
const LexApp = {
  config: {
    theme: localStorage.getItem('lex-theme') || 'light',
    sidebarCollapsed: false,
    apiBase: '/api/v1',
    csrfToken: document.querySelector('meta[name="csrf-token"]')?.content || ''
  },

  /** Initialize application */
  init() {
    this.initTheme();
    this.initSidebar();
    this.initToasts();
    this.initModals();
    this.initDropdowns();
    this.initForms();
    this.initHtmx();
    this.initKeyboardShortcuts();
    this.initSessionTimeout();
  },

  /** Theme management */
  initTheme() {
    document.documentElement.setAttribute('data-theme', this.config.theme);
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
      themeToggle.innerHTML = this.config.theme === 'dark'
        ? '<svg class="w-5 h-5"><use href="#icon-sun"/></svg>'
        : '<svg class="w-5 h-5"><use href="#icon-moon"/></svg>';
      themeToggle.addEventListener('click', () => this.toggleTheme());
    }
  },

  toggleTheme() {
    this.config.theme = this.config.theme === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', this.config.theme);
    localStorage.setItem('lex-theme', this.config.theme);
    this.initTheme();
  },

  /** Sidebar management */
  initSidebar() {
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.querySelector('.sidebar');
    if (sidebarToggle && sidebar) {
      sidebarToggle.addEventListener('click', () => {
        this.config.sidebarCollapsed = !this.config.sidebarCollapsed;
        sidebar.classList.toggle('collapsed', this.config.sidebarCollapsed);
      });
    }
  },

  /** Toast notification system */
  initToasts() {
    this.toastContainer = document.getElementById('toast-container') || this.createToastContainer();
  },

  createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
    return container;
  },

  showToast(message, type = 'info', title = null, duration = 5000) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
      <svg class="toast-icon"><use href="#icon-${type === 'error' ? 'alert' : type === 'success' ? 'check' : 'alert'}"/></svg>
      <div class="toast-content">
        ${title ? `<div class="toast-title">${title}</div>` : ''}
        <div class="toast-message">${message}</div>
      </div>
      <button class="modal-close" onclick="this.parentElement.remove()">
        <svg class="w-4 h-4"><use href="#icon-close"/></svg>
      </button>
    `;
    this.toastContainer.appendChild(toast);
    setTimeout(() => toast.classList.add('show'), 10);
    if (duration > 0) {
      setTimeout(() => this.dismissToast(toast), duration);
    }
  },

  dismissToast(toast) {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  },

  /** Modal management */
  initModals() {
    document.querySelectorAll('[data-modal]').forEach(trigger => {
      trigger.addEventListener('click', () => {
        const modalId = trigger.dataset.modal;
        this.openModal(modalId);
      });
    });

    document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
      backdrop.addEventListener('click', (e) => {
        if (e.target === backdrop) {
          this.closeModal(backdrop.id);
        }
      });
    });

    document.querySelectorAll('.modal-close').forEach(btn => {
      btn.addEventListener('click', () => {
        const modal = btn.closest('.modal-backdrop');
        if (modal) this.closeModal(modal.id);
      });
    });
  },

  openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.add('show');
  },

  closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.remove('show');
  },

  /** Dropdown management */
  initDropdowns() {
    document.querySelectorAll('.dropdown-toggle').forEach(toggle => {
      toggle.addEventListener('click', (e) => {
        e.stopPropagation();
        const menu = toggle.nextElementSibling;
        if (menu && menu.classList.contains('dropdown-menu')) {
          document.querySelectorAll('.dropdown-menu.show').forEach(m => {
            if (m !== menu) m.classList.remove('show');
          });
          menu.classList.toggle('show');
        }
      });
    });

    document.addEventListener('click', () => {
      document.querySelectorAll('.dropdown-menu.show').forEach(m => m.classList.remove('show'));
    });
  },

  /** Form handling */
  initForms() {
    document.querySelectorAll('form[data-async]').forEach(form => {
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(form);
        const url = form.action || window.location.href;
        const method = form.method || 'POST';
        const btn = form.querySelector('[type="submit"]');
        
        if (btn) btn.classList.add('btn-loading');
        
        try {
          const response = await fetch(url, {
            method,
            headers: {
              'Content-Type': 'application/json',
              'X-CSRF-Token': this.config.csrfToken,
              'Authorization': `Bearer ${LexAPI.getToken()}`
            },
            body: JSON.stringify(Object.fromEntries(formData))
          });

          const data = await response.json();
          
          if (response.ok) {
            this.showToast(data.message || 'Success', 'success');
            if (data.redirect) window.location.href = data.redirect;
          } else {
            this.showToast(data.message || 'An error occurred', 'error');
          }
        } catch (error) {
          this.showToast('Network error', 'error');
        } finally {
          if (btn) btn.classList.remove('btn-loading');
        }
      });
    });
  },

  /** HTMX initialization */
  initHtmx() {
    if (typeof htmx !== 'undefined') {
      htmx.config.defaultSwapStyle = 'innerHTML';
      htmx.config.defaultScrollBehavior = 'smooth';
      
      document.body.addEventListener('htmx:afterSwap', (e) => {
        this.initDropdowns();
        this.initModals();
      });

      document.body.addEventListener('htmx:responseError', (e) => {
        this.showToast('Request failed', 'error');
      });
    }
  },

  /** Keyboard shortcuts */
  initKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        document.querySelectorAll('.modal-backdrop.show, .dropdown-menu.show').forEach(el => {
          el.classList.remove('show');
        });
      }
      if (e.ctrlKey || e.metaKey) {
        if (e.key === '/') {
          e.preventDefault();
          document.querySelector('.search-input')?.focus();
        }
      }
    });
  },

  /** Session timeout warning */
  initSessionTimeout() {
    const warningTime = 5 * 60 * 1000;
    const logoutTime = 30 * 60 * 1000;
    let warningTimer, logoutTimer;

    const resetTimers = () => {
      clearTimeout(warningTimer);
      clearTimeout(logoutTimer);
      warningTimer = setTimeout(() => {
        this.showToast('Session expiring soon. Save your work.', 'warning', 'Session Timeout', 0);
        logoutTimer = setTimeout(() => {
          window.location.href = '/logout';
        }, warningTime);
      }, logoutTime - warningTime);
    };

    ['click', 'mousemove', 'keypress'].forEach(event => {
      document.addEventListener(event, resetTimers, { passive: true });
    });
  }
};

document.addEventListener('DOMContentLoaded', () => LexApp.init());