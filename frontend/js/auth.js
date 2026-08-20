/* ============================================
   Kalemna — Auth Module (auth.js)
   كلمنا — نظام التسجيل والدخول
   Frontend-only auth using localStorage.
   ============================================ */

import { ParticleSystem } from './particles.js';

// ─── Constants ───
const USERS_STORAGE_KEY = 'kalemna_users';
const CURRENT_USER_KEY = 'kalemna_current_user';

// ─── Initialize Particles ───
const particles = new ParticleSystem('particles-canvas');

// ─── Theme (respect saved theme) ───
const savedTheme = localStorage.getItem('kalemna-theme');
if (savedTheme) {
  document.documentElement.setAttribute('data-theme', savedTheme);
}

// ─── Utility Functions ───

/**
 * Gets all registered users from localStorage.
 * @returns {Array<{username: string, password: string, createdAt: string, provider: string}>}
 */
function getUsers() {
  try {
    return JSON.parse(localStorage.getItem(USERS_STORAGE_KEY)) || [];
  } catch {
    return [];
  }
}

/**
 * Saves users array to localStorage.
 * @param {Array} users
 */
function saveUsers(users) {
  localStorage.setItem(USERS_STORAGE_KEY, JSON.stringify(users));
}

/**
 * Sets the current logged-in user.
 * @param {object} user
 */
function setCurrentUser(user) {
  localStorage.setItem(CURRENT_USER_KEY, JSON.stringify({
    username: user.username,
    provider: user.provider || 'local',
    loggedInAt: new Date().toISOString(),
  }));
}

/**
 * Gets the current logged-in user.
 * @returns {object|null}
 */
function getCurrentUser() {
  try {
    return JSON.parse(localStorage.getItem(CURRENT_USER_KEY));
  } catch {
    return null;
  }
}

/**
 * Simple hash function for passwords (NOT cryptographically secure — frontend-only demo).
 * Uses a basic hash to avoid storing plaintext.
 * @param {string} str
 * @returns {string}
 */
function simpleHash(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32bit integer
  }
  return 'h_' + Math.abs(hash).toString(36) + '_' + str.length;
}

/**
 * Shows an error message on the page.
 * @param {string} message
 */
function showError(message) {
  const errorEl = document.getElementById('auth-error');
  const errorText = document.getElementById('auth-error-text');
  if (errorEl && errorText) {
    errorText.textContent = message;
    errorEl.style.display = 'flex';
    // Auto-hide after 5 seconds
    setTimeout(() => {
      errorEl.style.display = 'none';
    }, 5000);
  }
}

/**
 * Shows a success message on the page.
 * @param {string} message
 */
function showSuccess(message) {
  const successEl = document.getElementById('auth-success');
  const successText = document.getElementById('auth-success-text');
  if (successEl && successText) {
    successText.textContent = message;
    successEl.style.display = 'flex';
  }
}

/**
 * Hides error message.
 */
function hideError() {
  const errorEl = document.getElementById('auth-error');
  if (errorEl) errorEl.style.display = 'none';
}

/**
 * Evaluates password strength.
 * @param {string} password
 * @returns {{level: string, label: string}}
 */
function getPasswordStrength(password) {
  if (!password || password.length < 3) return { level: '', label: '' };

  let score = 0;
  if (password.length >= 6) score++;
  if (password.length >= 10) score++;
  if (/[A-Z]/.test(password)) score++;
  if (/[0-9]/.test(password)) score++;
  if (/[^A-Za-z0-9]/.test(password)) score++;

  if (score <= 1) return { level: 'weak', label: 'ضعيفة' };
  if (score <= 3) return { level: 'medium', label: 'متوسطة' };
  return { level: 'strong', label: 'قوية' };
}

/**
 * Sets the submit button loading state.
 * @param {HTMLElement} btn
 * @param {boolean} loading
 */
function setButtonLoading(btn, loading) {
  if (!btn) return;
  const textEl = btn.querySelector('.auth-form__submit-text');
  const loaderEl = btn.querySelector('.auth-form__submit-loader');
  if (loading) {
    btn.disabled = true;
    if (textEl) textEl.style.opacity = '0';
    if (loaderEl) loaderEl.style.display = 'flex';
  } else {
    btn.disabled = false;
    if (textEl) textEl.style.opacity = '1';
    if (loaderEl) loaderEl.style.display = 'none';
  }
}

// ─── If user is already logged in, redirect to chat ───
if (getCurrentUser()) {
  window.location.href = 'index.html';
}

// ─── DOM Ready ───
document.addEventListener('DOMContentLoaded', () => {
  // ────────────────────────
  // LOGIN PAGE
  // ────────────────────────
  const loginForm = document.getElementById('login-form');
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      hideError();

      const username = document.getElementById('login-username').value.trim();
      const password = document.getElementById('login-password').value;

      if (!username || !password) {
        showError('يرجى ملء جميع الحقول');
        return;
      }

      const submitBtn = document.getElementById('login-submit');
      setButtonLoading(submitBtn, true);

      // Simulate slight delay for UX
      await new Promise(r => setTimeout(r, 600));

      const users = getUsers();
      const hashedPassword = simpleHash(password);
      const user = users.find(u => u.username === username && u.password === hashedPassword);

      if (!user) {
        setButtonLoading(submitBtn, false);
        showError('اسم المستخدم أو كلمة المرور غير صحيحة');
        return;
      }

      setCurrentUser(user);
      setButtonLoading(submitBtn, false);

      // Redirect to chat
      window.location.href = 'index.html';
    });
  }

  // ────────────────────────
  // SIGNUP PAGE
  // ────────────────────────
  const signupForm = document.getElementById('signup-form');
  if (signupForm) {
    // Password strength indicator
    const passwordInput = document.getElementById('signup-password');
    const strengthFill = document.getElementById('strength-fill');
    const strengthLabel = document.getElementById('strength-label');

    if (passwordInput) {
      passwordInput.addEventListener('input', () => {
        const { level, label } = getPasswordStrength(passwordInput.value);
        if (strengthFill) {
          strengthFill.setAttribute('data-level', level);
        }
        if (strengthLabel) {
          strengthLabel.textContent = label;
        }
      });
    }

    signupForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      hideError();

      const username = document.getElementById('signup-username').value.trim();
      const password = document.getElementById('signup-password').value;
      const confirmPassword = document.getElementById('signup-confirm-password').value;

      // Validation
      if (!username || !password || !confirmPassword) {
        showError('يرجى ملء جميع الحقول');
        return;
      }

      if (username.length < 3) {
        showError('اسم المستخدم يجب أن يكون 3 أحرف على الأقل');
        return;
      }

      if (password.length < 6) {
        showError('كلمة المرور يجب أن تكون 6 أحرف على الأقل');
        return;
      }

      if (password !== confirmPassword) {
        showError('كلمة المرور غير متطابقة');
        return;
      }

      const submitBtn = document.getElementById('signup-submit');
      setButtonLoading(submitBtn, true);

      // Simulate slight delay for UX
      await new Promise(r => setTimeout(r, 800));

      const users = getUsers();

      // Check if username already exists
      if (users.find(u => u.username === username)) {
        setButtonLoading(submitBtn, false);
        showError('اسم المستخدم مستخدم بالفعل. اختر اسماً آخر.');
        return;
      }

      // Create new user
      const newUser = {
        username,
        password: simpleHash(password),
        createdAt: new Date().toISOString(),
        provider: 'local',
      };

      users.push(newUser);
      saveUsers(users);
      setCurrentUser(newUser);
      setButtonLoading(submitBtn, false);

      showSuccess('تم إنشاء الحساب بنجاح! جاري التحويل...');

      // Redirect to chat after brief delay
      setTimeout(() => {
        window.location.href = 'index.html';
      }, 1200);
    });
  }

  // ────────────────────────
  // GOOGLE SIGN-IN / SIGN-UP (Frontend Simulation)
  // ────────────────────────
  const googleLoginBtn = document.getElementById('google-login-btn');
  const googleSignupBtn = document.getElementById('google-signup-btn');

  function handleGoogleAuth() {
    hideError();

    // Since we can't actually implement Google OAuth without a backend,
    // we simulate the flow with a demo Google user.
    const googleUsername = 'google_user_' + Math.random().toString(36).substring(2, 6);
    const users = getUsers();

    const googleUser = {
      username: googleUsername,
      password: simpleHash('google_oauth_' + googleUsername),
      createdAt: new Date().toISOString(),
      provider: 'google',
    };

    // Check if a Google user is already saved (re-login)
    const existingGoogleUser = users.find(u => u.provider === 'google');
    if (existingGoogleUser) {
      setCurrentUser(existingGoogleUser);
    } else {
      users.push(googleUser);
      saveUsers(users);
      setCurrentUser(googleUser);
    }

    window.location.href = 'index.html';
  }

  if (googleLoginBtn) {
    googleLoginBtn.addEventListener('click', handleGoogleAuth);
  }

  if (googleSignupBtn) {
    googleSignupBtn.addEventListener('click', handleGoogleAuth);
  }

  // ────────────────────────
  // TOGGLE PASSWORD VISIBILITY
  // ────────────────────────
  const togglePassBtns = document.querySelectorAll('.auth-form__toggle-pass');
  togglePassBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const wrapper = btn.closest('.auth-form__input-wrapper');
      const input = wrapper?.querySelector('input[type="password"], input[type="text"]');
      if (input) {
        const isPassword = input.type === 'password';
        input.type = isPassword ? 'text' : 'password';
        // Toggle icon appearance
        btn.style.opacity = isPassword ? '1' : '0.5';
      }
    });
  });
});
