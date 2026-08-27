/* ============================================
   Kalemna — Auth Module (auth.js)
   كلمنا — نظام التسجيل والدخول
   Real backend integration with JWT auth.
   ============================================ */

import { ParticleSystem } from './particles.js';
import {
  loginUser,
  signupUser,
  saveAuthData,
  getAuthData,
  isTokenExpired
} from './api.js';

// ─── Initialize Particles ───
const particles = new ParticleSystem('particles-canvas');

// ─── Theme (respect saved theme) ───
const savedTheme = localStorage.getItem('kalemna-theme');
if (savedTheme) {
  document.documentElement.setAttribute('data-theme', savedTheme);
}


// ═══════════════════════════════════════════
// VALIDATION HELPERS
// ═══════════════════════════════════════════

/**
 * Email validation regex.
 * @param {string} email
 * @returns {boolean}
 */
function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

/**
 * Phone validation regex (matches backend: ^\+?[0-9]{10,15}$).
 * @param {string} phone
 * @returns {boolean}
 */
function isValidPhone(phone) {
  return /^\+?[0-9]{10,15}$/.test(phone);
}

/**
 * Username validation: 3-50 chars, alphanumeric + underscore.
 * @param {string} username
 * @returns {boolean}
 */
function isValidUsername(username) {
  return username.length >= 3 && username.length <= 50;
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


// ═══════════════════════════════════════════
// UI HELPERS
// ═══════════════════════════════════════════

/**
 * Shows an error message on the page (top-level banner).
 * @param {string} message
 */
function showError(message) {
  const errorEl = document.getElementById('auth-error');
  const errorText = document.getElementById('auth-error-text');
  if (errorEl && errorText) {
    errorText.textContent = message;
    errorEl.style.display = 'flex';
    // Auto-hide after 7 seconds
    setTimeout(() => {
      errorEl.style.display = 'none';
    }, 7000);
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
 * Shows a field-level validation error.
 * @param {string} inputId - The input element ID
 * @param {string} message - Error message to display
 */
function showFieldError(inputId, message) {
  const input = document.getElementById(inputId);
  if (!input) return;

  const wrapper = input.closest('.auth-form__input-wrapper');
  if (wrapper) {
    wrapper.classList.add('auth-form__input-wrapper--error');
    wrapper.classList.remove('auth-form__input-wrapper--success');
  }

  // Look for a sibling field-error span
  const errorSpan = wrapper?.parentElement?.querySelector('.auth-form__field-error');
  if (errorSpan) {
    errorSpan.textContent = message;
    errorSpan.style.display = 'block';
  }
}

/**
 * Shows a field-level success state.
 * @param {string} inputId - The input element ID
 */
function showFieldSuccess(inputId) {
  const input = document.getElementById(inputId);
  if (!input) return;

  const wrapper = input.closest('.auth-form__input-wrapper');
  if (wrapper) {
    wrapper.classList.remove('auth-form__input-wrapper--error');
    wrapper.classList.add('auth-form__input-wrapper--success');
  }

  const errorSpan = wrapper?.parentElement?.querySelector('.auth-form__field-error');
  if (errorSpan) {
    errorSpan.textContent = '';
    errorSpan.style.display = 'none';
  }
}

/**
 * Clears all field-level validation states.
 */
function clearFieldErrors() {
  document.querySelectorAll('.auth-form__input-wrapper').forEach(wrapper => {
    wrapper.classList.remove('auth-form__input-wrapper--error', 'auth-form__input-wrapper--success');
  });
  document.querySelectorAll('.auth-form__field-error').forEach(span => {
    span.textContent = '';
    span.style.display = 'none';
  });
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


// ═══════════════════════════════════════════
// AUTH GUARD — Redirect logged-in users to chat
// ═══════════════════════════════════════════
const authData = getAuthData();
if (authData && authData.access_token && !isTokenExpired()) {
  window.location.href = 'index.html';
}


// ═══════════════════════════════════════════
// DOM READY — Bind Form Handlers
// ═══════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {

  // ────────────────────────
  // LOGIN PAGE
  // ────────────────────────
  const loginForm = document.getElementById('login-form');
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      hideError();
      clearFieldErrors();

      const usernameInput = document.getElementById('login-username');
      const passwordInput = document.getElementById('login-password');
      const username = usernameInput.value.trim();
      const password = passwordInput.value;

      // ─── Frontend Validation ───
      let hasErrors = false;

      if (!username) {
        showFieldError('login-username', 'يرجى إدخال اسم المستخدم');
        hasErrors = true;
      } else if (username.length < 3) {
        showFieldError('login-username', 'اسم المستخدم يجب أن يكون 3 أحرف على الأقل');
        hasErrors = true;
      } else {
        showFieldSuccess('login-username');
      }

      if (!password) {
        showFieldError('login-password', 'يرجى إدخال كلمة المرور');
        hasErrors = true;
      } else if (password.length < 6) {
        showFieldError('login-password', 'كلمة المرور يجب أن تكون 6 أحرف على الأقل');
        hasErrors = true;
      } else {
        showFieldSuccess('login-password');
      }

      if (hasErrors) return;

      // ─── Call Backend /login ───
      const submitBtn = document.getElementById('login-submit');
      setButtonLoading(submitBtn, true);

      try {
        const result = await loginUser(username, password);

        // result = { access_token: "...", token_type: "Bearer" }
        saveAuthData(result.access_token, username);

        // Redirect to chat
        window.location.href = 'index.html';
      } catch (error) {
        setButtonLoading(submitBtn, false);
        showError(error.message);
      }
    });

    // ─── Live Validation on blur ───
    const loginUsername = document.getElementById('login-username');
    const loginPassword = document.getElementById('login-password');

    if (loginUsername) {
      loginUsername.addEventListener('blur', () => {
        const val = loginUsername.value.trim();
        if (val && val.length < 3) {
          showFieldError('login-username', 'اسم المستخدم يجب أن يكون 3 أحرف على الأقل');
        } else if (val) {
          showFieldSuccess('login-username');
        }
      });
    }

    if (loginPassword) {
      loginPassword.addEventListener('blur', () => {
        const val = loginPassword.value;
        if (val && val.length < 6) {
          showFieldError('login-password', 'كلمة المرور يجب أن تكون 6 أحرف على الأقل');
        } else if (val) {
          showFieldSuccess('login-password');
        }
      });
    }
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
      clearFieldErrors();

      const username = document.getElementById('signup-username').value.trim();
      const password = document.getElementById('signup-password').value;
      const confirmPassword = document.getElementById('signup-confirm-password').value;
      const email = document.getElementById('signup-email')?.value.trim() || '';
      const phone = document.getElementById('signup-phone')?.value.trim() || '';

      // ─── Frontend Validation ───
      let hasErrors = false;

      // Username
      if (!username) {
        showFieldError('signup-username', 'يرجى إدخال اسم المستخدم');
        hasErrors = true;
      } else if (!isValidUsername(username)) {
        showFieldError('signup-username', 'اسم المستخدم يجب أن يكون بين 3 و 50 حرف');
        hasErrors = true;
      } else {
        showFieldSuccess('signup-username');
      }

      // Password
      if (!password) {
        showFieldError('signup-password', 'يرجى إدخال كلمة المرور');
        hasErrors = true;
      } else if (password.length < 6) {
        showFieldError('signup-password', 'كلمة المرور يجب أن تكون 6 أحرف على الأقل');
        hasErrors = true;
      } else {
        showFieldSuccess('signup-password');
      }

      // Confirm Password
      if (!confirmPassword) {
        showFieldError('signup-confirm-password', 'يرجى تأكيد كلمة المرور');
        hasErrors = true;
      } else if (password !== confirmPassword) {
        showFieldError('signup-confirm-password', 'كلمة المرور غير متطابقة');
        hasErrors = true;
      } else if (password) {
        showFieldSuccess('signup-confirm-password');
      }

      // Email
      if (!email) {
        showFieldError('signup-email', 'يرجى إدخال البريد الإلكتروني');
        hasErrors = true;
      } else if (!isValidEmail(email)) {
        showFieldError('signup-email', 'صيغة البريد الإلكتروني غير صحيحة');
        hasErrors = true;
      } else {
        showFieldSuccess('signup-email');
      }

      // Phone
      if (!phone) {
        showFieldError('signup-phone', 'يرجى إدخال رقم الهاتف');
        hasErrors = true;
      } else if (!isValidPhone(phone)) {
        showFieldError('signup-phone', 'رقم الهاتف غير صحيح (مثال: +201234567890)');
        hasErrors = true;
      } else {
        showFieldSuccess('signup-phone');
      }

      if (hasErrors) return;

      // ─── Call Backend /signup ───
      const submitBtn = document.getElementById('signup-submit');
      setButtonLoading(submitBtn, true);

      try {
        const result = await signupUser({
          username,
          password,
          email,
          phone,
        });

        // result = { message: "User created successfully", access_token: "..." }
        saveAuthData(result.access_token, username);

        setButtonLoading(submitBtn, false);
        showSuccess('تم إنشاء الحساب بنجاح! جاري التحويل...');

        // Redirect to chat after brief delay
        setTimeout(() => {
          window.location.href = 'index.html';
        }, 1200);
      } catch (error) {
        setButtonLoading(submitBtn, false);
        showError(error.message);
      }
    });

    // ─── Live Validation on blur ───
    const signupUsername = document.getElementById('signup-username');
    const signupPassword = document.getElementById('signup-password');
    const signupConfirm = document.getElementById('signup-confirm-password');
    const signupEmail = document.getElementById('signup-email');
    const signupPhone = document.getElementById('signup-phone');

    if (signupUsername) {
      signupUsername.addEventListener('blur', () => {
        const val = signupUsername.value.trim();
        if (val && !isValidUsername(val)) {
          showFieldError('signup-username', 'اسم المستخدم يجب أن يكون بين 3 و 50 حرف');
        } else if (val) {
          showFieldSuccess('signup-username');
        }
      });
    }

    if (signupPassword) {
      signupPassword.addEventListener('blur', () => {
        const val = signupPassword.value;
        if (val && val.length < 6) {
          showFieldError('signup-password', 'كلمة المرور يجب أن تكون 6 أحرف على الأقل');
        } else if (val) {
          showFieldSuccess('signup-password');
        }
      });
    }

    if (signupConfirm) {
      signupConfirm.addEventListener('blur', () => {
        const val = signupConfirm.value;
        const pass = signupPassword?.value || '';
        if (val && val !== pass) {
          showFieldError('signup-confirm-password', 'كلمة المرور غير متطابقة');
        } else if (val && val === pass) {
          showFieldSuccess('signup-confirm-password');
        }
      });
    }

    if (signupEmail) {
      signupEmail.addEventListener('blur', () => {
        const val = signupEmail.value.trim();
        if (val && !isValidEmail(val)) {
          showFieldError('signup-email', 'صيغة البريد الإلكتروني غير صحيحة');
        } else if (val) {
          showFieldSuccess('signup-email');
        }
      });
    }

    if (signupPhone) {
      signupPhone.addEventListener('blur', () => {
        const val = signupPhone.value.trim();
        if (val && !isValidPhone(val)) {
          showFieldError('signup-phone', 'رقم الهاتف غير صحيح (مثال: +201234567890)');
        } else if (val) {
          showFieldSuccess('signup-phone');
        }
      });
    }
  }


  // ────────────────────────
  // GOOGLE SIGN-IN / SIGN-UP (Placeholder — needs backend OAuth)
  // ────────────────────────
  const googleLoginBtn = document.getElementById('google-login-btn');
  const googleSignupBtn = document.getElementById('google-signup-btn');

  function handleGoogleAuth() {
    hideError();
    // Google OAuth requires backend implementation.
    // Show informational message.
    showError('تسجيل الدخول عبر Google غير متاح حالياً. استخدم اسم المستخدم وكلمة المرور');
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
