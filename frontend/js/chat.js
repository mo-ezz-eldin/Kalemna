/* ============================================
   Kalemna — Chat Engine (chat.js)
   كلمنا — محرك المحادثة
   ============================================ */

import { sendMessage, sendChatMessage } from './api.js';
import { getUserIdFromToken } from './api.js';
import { escapeHTML, relativeTime, renderMarkdownLite, generateId, SENTIMENT_MAP } from './utils.js';

export class ChatEngine {
  constructor() {
    this.messagesContainer = document.getElementById('chat-messages');
    this.welcomeScreen = document.getElementById('welcome-screen');
    this.inputTextarea = document.getElementById('chat-input');
    this.sendBtn = document.getElementById('btn-send');
    this.messages = [];
    this.isProcessing = false;
    // Use real user_id from JWT (set by index.html auth guard or decoded from token)
    this.conversationId = window.__kalemnaUserId || getUserIdFromToken() || generateId();
    this._timeUpdateInterval = null;
  }

  /**
   * Initializes the chat with a welcome screen.
   */
  init() {
    this._showWelcome();
    this._updateSendButton();
    this._startTimeUpdater();
  }

  /**
   * Sends a user message and gets AI response via stream.
   * @param {string} text
   */
  async send(text) {
    const trimmed = text.trim();
    if (!trimmed || this.isProcessing) return;

    this.isProcessing = true;
    this._updateSendButton();
    this._hideWelcome();

    // Add user message
    this._addMessage('user', trimmed);

    // Clear input
    this.inputTextarea.value = '';
    this.inputTextarea.style.height = 'auto';

    // Show typing indicator
    const typingEl = this._showTyping();

    let botMsgId = null;
    let fullBotText = '';

    try {
      await sendChatMessage(trimmed, this.conversationId, (token) => {
        if (!botMsgId) {
          this._removeTyping(typingEl);
          botMsgId = generateId();
          const msg = {
            id: botMsgId,
            role: 'ai',
            text: '',
            timestamp: new Date(),
          };
          this.messages.push(msg);
          this._renderMessage(msg);
        }

        fullBotText += token;

        // Update message content
        const msg = this.messages.find(m => m.id === botMsgId);
        if (msg) {
          msg.text = fullBotText;
        }

        const el = document.getElementById(`msg-${botMsgId}`);
        if (el) {
          const bubble = el.querySelector('.message__bubble');
          if (bubble) {
            bubble.innerHTML = renderMarkdownLite(fullBotText);
          }
        }
        this._scrollToBottom();
      });

      if (!botMsgId) {
        this._removeTyping(typingEl);
        this._addMessage('ai', 'عذراً، لم يتم استلام أي رد.');
      }
    } catch (error) {
      this._removeTyping(typingEl);
      this._showError(error.message, trimmed);
    } finally {
      this.isProcessing = false;
      this._updateSendButton();
    }
  }

  /**
   * Extracts text from various response shapes.
   * @param {object} response
   * @returns {string}
   */
  _extractResponseText(response) {
    // The /final_prediction endpoint may return different shapes
    if (typeof response === 'string') return response;
    if (response.data) {
      if (typeof response.data === 'string') return response.data;
      if (response.data.response) return response.data.response;
      if (response.data.text) return response.data.text;
      return JSON.stringify(response.data);
    }
    if (response.response) return response.response;
    if (response.text) return response.text;
    if (response.action) {
      return `الإجراء: ${response.action}`;
    }
    return JSON.stringify(response);
  }

  /**
   * Extracts sentiment from response if available.
   * @param {object} response
   * @returns {string|null}
   */
  _extractSentiment(response) {
    if (response.data && response.data.sentiment) return response.data.sentiment;
    if (response.sentiment) return response.sentiment;
    if (response.final_sentiment) return response.final_sentiment;
    return null;
  }

  /**
   * Adds a message to the chat.
   * @param {'user'|'ai'} role
   * @param {string} text
   * @param {object} metadata
   */
  _addMessage(role, text, metadata = {}) {
    const msg = {
      id: generateId(),
      role,
      text,
      timestamp: new Date(),
      ...metadata,
    };

    this.messages.push(msg);
    this._renderMessage(msg);
    this._scrollToBottom();
  }

  /**
   * Renders a single message to the DOM.
   * @param {object} msg
   */
  _renderMessage(msg) {
    const el = document.createElement('div');
    el.className = `message message--${msg.role}`;
    el.id = `msg-${msg.id}`;

    const avatar = document.createElement('div');
    avatar.className = 'message__avatar';
    avatar.textContent = msg.role === 'user' ? '👤' : '🤖';

    const content = document.createElement('div');
    content.className = 'message__content';

    const bubble = document.createElement('div');
    bubble.className = 'message__bubble';
    bubble.setAttribute('dir', 'rtl');

    if (msg.role === 'ai' && msg.sentiment && SENTIMENT_MAP[msg.sentiment]) {
      bubble.classList.add('message__bubble--sentiment');
      bubble.style.setProperty('--sentiment-color', SENTIMENT_MAP[msg.sentiment].color);
    }

    if (msg.role === 'ai') {
      bubble.innerHTML = renderMarkdownLite(msg.text);
    } else {
      bubble.textContent = msg.text;
    }

    const meta = document.createElement('div');
    meta.className = 'message__meta';

    const time = document.createElement('span');
    time.className = 'message__time';
    time.setAttribute('data-timestamp', new Date(msg.timestamp).toISOString());
    time.textContent = relativeTime(msg.timestamp);

    meta.appendChild(time);

    // Add sentiment badge for AI messages
    if (msg.role === 'ai' && msg.sentiment && SENTIMENT_MAP[msg.sentiment]) {
      const sentimentInfo = SENTIMENT_MAP[msg.sentiment];
      const badge = document.createElement('span');
      badge.className = 'sentiment-badge';
      badge.style.setProperty('--sentiment-color', sentimentInfo.color);
      badge.style.setProperty('--sentiment-bg', sentimentInfo.color.replace(')', ', 0.12)').replace('var(', '').replace(')', ')'));
      badge.innerHTML = `<span class="sentiment-badge__emoji">${sentimentInfo.emoji}</span> ${sentimentInfo.label}`;
      meta.appendChild(badge);
    }

    content.appendChild(bubble);
    content.appendChild(meta);

    el.appendChild(avatar);
    el.appendChild(content);

    this.messagesContainer.appendChild(el);
  }

  /**
   * Shows the typing indicator.
   * @returns {HTMLElement}
   */
  _showTyping() {
    const el = document.createElement('div');
    el.className = 'typing-indicator';
    el.id = 'typing-indicator';

    const avatar = document.createElement('div');
    avatar.className = 'message__avatar';
    avatar.textContent = '🤖';

    const bubble = document.createElement('div');
    bubble.className = 'typing-indicator__bubble';
    bubble.innerHTML = `
      <div class="typing-indicator__dot"></div>
      <div class="typing-indicator__dot"></div>
      <div class="typing-indicator__dot"></div>
    `;

    el.appendChild(avatar);
    el.appendChild(bubble);

    this.messagesContainer.appendChild(el);
    this._scrollToBottom();

    return el;
  }

  /**
   * Removes the typing indicator.
   * @param {HTMLElement} el
   */
  _removeTyping(el) {
    if (el && el.parentNode) {
      el.parentNode.removeChild(el);
    }
  }

  /**
   * Shows an error message with retry option.
   * @param {string} message
   * @param {string} originalText
   */
  _showError(message, originalText) {
    const el = document.createElement('div');
    el.className = 'error-message';
    el.innerHTML = `
      <span class="error-message__icon">⚠️</span>
      <span>${escapeHTML(message)}</span>
      <button class="error-message__retry" id="retry-${generateId()}">إعادة المحاولة</button>
    `;

    this.messagesContainer.appendChild(el);
    this._scrollToBottom();

    // Retry handler
    const retryBtn = el.querySelector('.error-message__retry');
    retryBtn.addEventListener('click', () => {
      el.remove();
      this.send(originalText);
    });
  }

  /**
   * Shows the welcome screen.
   */
  _showWelcome() {
    if (this.welcomeScreen) {
      this.welcomeScreen.style.display = 'flex';
    }
  }

  /**
   * Hides the welcome screen.
   */
  _hideWelcome() {
    if (this.welcomeScreen) {
      this.welcomeScreen.style.display = 'none';
    }
  }

  /**
   * Scrolls chat to the bottom smoothly.
   */
  _scrollToBottom() {
    const chatArea = this.messagesContainer.closest('.chat-area');
    if (chatArea) {
      requestAnimationFrame(() => {
        chatArea.scrollTo({
          top: chatArea.scrollHeight,
          behavior: 'smooth',
        });
      });
    }
  }

  /**
   * Updates the send button state.
   */
  _updateSendButton() {
    if (this.sendBtn) {
      this.sendBtn.disabled = this.isProcessing;
    }
  }

  /**
   * Starts an interval that updates all message timestamps every 30 seconds.
   */
  _startTimeUpdater() {
    if (this._timeUpdateInterval) {
      clearInterval(this._timeUpdateInterval);
    }
    this._timeUpdateInterval = setInterval(() => {
      this._updateAllTimes();
    }, 30000); // Update every 30 seconds
  }

  /**
   * Updates all visible message time labels with fresh relative times.
   */
  _updateAllTimes() {
    const timeElements = this.messagesContainer.querySelectorAll('.message__time[data-timestamp]');
    timeElements.forEach(el => {
      const timestamp = el.getAttribute('data-timestamp');
      if (timestamp) {
        el.textContent = relativeTime(new Date(timestamp));
      }
    });
  }

  /**
   * Clears the chat and starts a new conversation.
   */
  newChat() {
    this.messages = [];
    // Keep the same user_id — backend handles conversation history per user
    this.conversationId = window.__kalemnaUserId || getUserIdFromToken() || generateId();
    this.messagesContainer.innerHTML = '';
    this._showWelcome();
  }
}
