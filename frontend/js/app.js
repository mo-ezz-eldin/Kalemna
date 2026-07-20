/* ============================================
   Kalemna — App Initialization (app.js)
   كلمنا — التهيئة الرئيسية
   ============================================ */

import { ThemeManager } from './theme.js';
import { ChatEngine } from './chat.js';
import { ParticleSystem } from './particles.js';
import { autoResizeTextarea } from './utils.js';

class KalemnaApp {
  constructor() {
    this.theme = new ThemeManager();
    this.chat = new ChatEngine();
    this.particles = new ParticleSystem('particles-canvas');

    this._bindEvents();
    this.chat.init();
  }

  _bindEvents() {
    // ─── Theme Toggle ───
    const themeBtn = document.getElementById('theme-toggle');
    if (themeBtn) {
      themeBtn.addEventListener('click', () => this.theme.toggle());
    }

    // ─── Send Message ───
    const sendBtn = document.getElementById('btn-send');
    if (sendBtn) {
      sendBtn.addEventListener('click', () => this._handleSend());
    }

    // ─── Chat Input ───
    const input = document.getElementById('chat-input');
    if (input) {
      input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          this._handleSend();
        }
      });

      input.addEventListener('input', () => {
        autoResizeTextarea(input);
      });
    }

    // ─── New Chat ───
    const newChatBtn = document.getElementById('btn-new-chat');
    if (newChatBtn) {
      newChatBtn.addEventListener('click', () => this.chat.newChat());
    }

    // ─── Sidebar Toggle (Mobile) ───
    const menuToggle = document.getElementById('menu-toggle');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');

    if (menuToggle && sidebar) {
      menuToggle.addEventListener('click', () => this._toggleSidebar());
    }

    if (overlay) {
      overlay.addEventListener('click', () => this._closeSidebar());
    }

    // ─── Sidebar Close Button ───
    const sidebarClose = document.getElementById('sidebar-close');
    if (sidebarClose) {
      sidebarClose.addEventListener('click', () => this._closeSidebar());
    }

    // ─── Welcome Suggestion Chips ───
    document.querySelectorAll('.welcome__chip').forEach(chip => {
      chip.addEventListener('click', () => {
        const text = chip.getAttribute('data-message');
        if (text && input) {
          input.value = text;
          autoResizeTextarea(input);
          input.focus();
        }
      });
    });

    // ─── Keyboard Shortcuts ───
    document.addEventListener('keydown', (e) => {
      // Escape closes sidebar on mobile
      if (e.key === 'Escape') {
        this._closeSidebar();
      }
    });
  }

  _handleSend() {
    const input = document.getElementById('chat-input');
    if (input && input.value.trim()) {
      this.chat.send(input.value);
    }
  }

  _toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');

    if (sidebar) {
      sidebar.classList.toggle('open');
    }
    if (overlay) {
      overlay.classList.toggle('active');
    }
  }

  _closeSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');

    if (sidebar) {
      sidebar.classList.remove('open');
    }
    if (overlay) {
      overlay.classList.remove('active');
    }
  }
}

// ─── Initialize on DOM ready ───
document.addEventListener('DOMContentLoaded', () => {
  window.kalemnaApp = new KalemnaApp();
});
