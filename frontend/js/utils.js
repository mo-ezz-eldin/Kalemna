/* ============================================
   Kalemna — Utilities (utils.js)
   كلمنا — أدوات مساعدة
   ============================================ */

/**
 * Checks if text is predominantly Arabic.
 * @param {string} text
 * @returns {boolean}
 */
export function isArabic(text) {
  if (!text) return false;
  const arabicPattern = /[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]/g;
  const matches = text.match(arabicPattern);
  if (!matches) return false;
  const letterChars = text.replace(/[\s\d\W]/g, '');
  return letterChars.length > 0 && matches.length / letterChars.length > 0.3;
}

/**
 * Returns a human-readable relative time string in Arabic.
 * @param {Date|string|number} date
 * @returns {string}
 */
export function relativeTime(date) {
  const now = new Date();
  const then = new Date(date);
  const diffMs = now - then;
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHr = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHr / 24);

  if (diffSec < 10) return 'الآن';
  if (diffSec < 60) return `منذ ${diffSec} ثانية`;
  if (diffMin < 60) return `منذ ${diffMin} دقيقة`;
  if (diffHr < 24) return `منذ ${diffHr} ساعة`;
  if (diffDay < 7) return `منذ ${diffDay} يوم`;
  return then.toLocaleDateString('ar-EG');
}

/**
 * Escapes HTML entities to prevent XSS.
 * @param {string} str
 * @returns {string}
 */
export function escapeHTML(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

/**
 * Auto-resizes a textarea to fit its content.
 * @param {HTMLTextAreaElement} el
 */
export function autoResizeTextarea(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 150) + 'px';
}

/**
 * Standard debounce utility.
 * @param {Function} fn
 * @param {number} ms
 * @returns {Function}
 */
export function debounce(fn, ms) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
}

/**
 * Generates a simple unique ID.
 * @returns {string}
 */
export function generateId() {
  return Date.now().toString(36) + Math.random().toString(36).substring(2, 7);
}

/**
 * Renders basic markdown-like formatting to HTML.
 * Supports: **bold**, *italic*, `code`, line breaks.
 * @param {string} text
 * @returns {string}
 */
export function renderMarkdownLite(text) {
  if (!text) return '';
  let html = escapeHTML(text);
  // Bold: **text**
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  // Italic: *text*
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
  // Inline code: `code`
  html = html.replace(/`(.+?)`/g, '<code>$1</code>');
  // Line breaks
  html = html.replace(/\n/g, '<br>');
  return html;
}

/**
 * Maps sentiment keys to their display info.
 */
export const SENTIMENT_MAP = {
  joy:      { emoji: '😊', label: 'سعادة', color: 'var(--sentiment-joy)' },
  neutral:  { emoji: '😐', label: 'محايد', color: 'var(--sentiment-neutral)' },
  anger:    { emoji: '😠', label: 'غضب', color: 'var(--sentiment-anger)' },
  disgust:  { emoji: '🤢', label: 'اشمئزاز', color: 'var(--sentiment-disgust)' },
  fear:     { emoji: '😨', label: 'خوف', color: 'var(--sentiment-fear)' },
  sadness:  { emoji: '😢', label: 'حزن', color: 'var(--sentiment-sadness)' },
  surprise: { emoji: '😲', label: 'دهشة', color: 'var(--sentiment-surprise)' },
};
