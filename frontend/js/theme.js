/* ============================================
   Kalemna — Theme Manager (theme.js)
   كلمنا — مدير السمات
   ============================================ */

const THEME_KEY = 'kalemna-theme';
const THEMES = ['dark', 'light', 'midnight'];

const THEME_ICONS = {
  dark: '🌙',
  light: '☀️',
  midnight: '🌌',
};

const THEME_LABELS = {
  dark: 'داكن',
  light: 'فاتح',
  midnight: 'منتصف الليل',
};

export class ThemeManager {
  constructor() {
    this.currentTheme = this._loadTheme();
    this._applyTheme(this.currentTheme);
    this._updateToggleButton();
  }

  /**
   * Loads the saved theme or detects from system preference.
   * @returns {string}
   */
  _loadTheme() {
    const saved = localStorage.getItem(THEME_KEY);
    if (saved && THEMES.includes(saved)) return saved;

    // Detect system preference
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
      return 'light';
    }
    return 'dark';
  }

  /**
   * Applies the theme to the document.
   * @param {string} theme
   */
  _applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);

    // Dispatch event for other modules (like particles)
    window.dispatchEvent(new CustomEvent('themechange', { detail: { theme } }));
  }

  /**
   * Updates the toggle button icon.
   */
  _updateToggleButton() {
    const btn = document.getElementById('theme-toggle');
    if (!btn) return;

    const iconEl = btn.querySelector('.theme-toggle__icon');
    if (iconEl) {
      iconEl.textContent = THEME_ICONS[this.currentTheme];
    }

    btn.setAttribute('data-tooltip', `السمة: ${THEME_LABELS[this.currentTheme]}`);
  }

  /**
   * Cycles to the next theme.
   */
  toggle() {
    const currentIndex = THEMES.indexOf(this.currentTheme);
    const nextIndex = (currentIndex + 1) % THEMES.length;
    this.currentTheme = THEMES[nextIndex];

    localStorage.setItem(THEME_KEY, this.currentTheme);
    this._applyTheme(this.currentTheme);
    this._updateToggleButton();
  }

  /**
   * Returns the current theme name.
   * @returns {string}
   */
  getTheme() {
    return this.currentTheme;
  }
}
