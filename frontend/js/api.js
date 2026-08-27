/* ============================================
   Kalemna — API Client (api.js)
   كلمنا — عميل الواجهة البرمجية
   ============================================ */

const API_BASE_URL = 'http://localhost:8000';
const REQUEST_TIMEOUT = 600000;
const CURRENT_USER_KEY = 'kalemna_current_user';

// ═══════════════════════════════════════════
// ERROR MAPPING — Backend HTTPException → Friendly Arabic
// ═══════════════════════════════════════════

/**
 * Maps backend `detail` strings to user-friendly Arabic messages.
 * Covers all HTTPException cases from auth.py, chat.py, and user_security_credentials.py.
 */
const ERROR_MAP = {
  // Auth: POST /login (401)
  'Incorrect username or password': 'اسم المستخدم أو كلمة المرور غير صحيحة',

  // Auth: POST /signup (409)
  'Username already exists': 'اسم المستخدم مستخدم بالفعل. اختر اسماً آخر',

  // Auth: POST /signup (500)
  'Database error occurred': 'حدث خطأ في قاعدة البيانات. حاول مرة أخرى لاحقاً',

  // Chat: JWT validation (401)
  'could not validate credentials': 'انتهت جلستك. يرجى تسجيل الدخول مرة أخرى',

  // Chat: JWT expired (401)
  'Token has expired': 'انتهت صلاحية الجلسة. يرجى تسجيل الدخول مرة أخرى',
};

/**
 * Maps Pydantic field names to Arabic labels for 422 validation errors.
 */
const FIELD_LABEL_MAP = {
  username: 'اسم المستخدم',
  password: 'كلمة المرور',
  email: 'البريد الإلكتروني',
  phone: 'رقم الهاتف',
  default_address: 'العنوان',
  text: 'نص الرسالة',
};

/**
 * Extracts a friendly Arabic error message from a backend response.
 * Handles: 401, 409, 422, 429, 500 and generic errors.
 * @param {Response} response - The fetch Response object
 * @param {object|null} errorBody - The parsed JSON error body (if available)
 * @returns {string} A user-friendly Arabic error message
 */
function mapBackendError(response, errorBody) {
  const status = response.status;

  // ─── 422: Pydantic Validation Errors ───
  if (status === 422 && errorBody && errorBody.detail && Array.isArray(errorBody.detail)) {
    const messages = errorBody.detail.map(err => {
      const fieldName = err.loc && err.loc.length > 1 ? err.loc[err.loc.length - 1] : 'unknown';
      const arabicLabel = FIELD_LABEL_MAP[fieldName] || fieldName;

      // Map common Pydantic error types to Arabic
      const errType = err.type || '';
      if (errType === 'string_too_short') {
        return `${arabicLabel}: يجب أن يكون ${err.ctx?.min_length || 3} أحرف على الأقل`;
      }
      if (errType === 'string_too_long') {
        return `${arabicLabel}: يجب ألا يتجاوز ${err.ctx?.max_length || 50} حرف`;
      }
      if (errType === 'value_error' || errType === 'value_error.email') {
        return `${arabicLabel}: القيمة غير صالحة`;
      }
      if (errType === 'string_pattern_mismatch') {
        return `${arabicLabel}: الصيغة غير صحيحة`;
      }
      if (errType === 'missing') {
        return `${arabicLabel}: هذا الحقل مطلوب`;
      }

      return `${arabicLabel}: ${err.msg || 'قيمة غير صالحة'}`;
    });

    return messages.join('\n');
  }

  // ─── 429: Rate Limit Exceeded ───
  if (status === 429) {
    return 'لقد تجاوزت الحد المسموح من الطلبات. انتظر قليلاً ثم حاول مرة أخرى';
  }

  // ─── Detail-based mapping (401, 409, 500, etc.) ───
  if (errorBody && errorBody.detail) {
    const detail = typeof errorBody.detail === 'string' ? errorBody.detail : JSON.stringify(errorBody.detail);
    if (ERROR_MAP[detail]) {
      return ERROR_MAP[detail];
    }
    // If the detail has a message field
    if (errorBody.detail.message) {
      return errorBody.detail.message;
    }
  }

  // ─── message-based mapping (from exception_handler) ───
  if (errorBody && errorBody.message) {
    return errorBody.message;
  }

  // ─── Generic fallbacks by status code ───
  if (status === 401) return 'غير مصرح لك. يرجى تسجيل الدخول مرة أخرى';
  if (status === 403) return 'ليس لديك صلاحية للقيام بهذا الإجراء';
  if (status === 404) return 'الصفحة أو المورد المطلوب غير موجود';
  if (status === 500) return 'عذراً، حدث خطأ تقني. جاري العمل على حله';
  if (status === 503) return 'الخدمة غير متاحة حالياً. حاول مرة أخرى لاحقاً';

  return `خطأ غير متوقع (${status}). حاول مرة أخرى`;
}


// ══════════════════════════════════════════
// AUTH HELPERS
// ══════════════════════════════════════════

/**
 * Gets the stored auth data from localStorage.
 * @returns {{access_token: string, username: string, user_id: string}|null}
 */
export function getAuthData() {
  try {
    return JSON.parse(localStorage.getItem(CURRENT_USER_KEY));
  } catch {
    return null;
  }
}

/**
 * Gets the JWT access token from localStorage.
 * @returns {string|null}
 */
export function getAuthToken() {
  const data = getAuthData();
  return data?.access_token || null;
}

/**
 * Decodes a JWT payload without verifying the signature (client-side only).
 * @param {string} token
 * @returns {object|null}
 */
export function decodeJWT(token) {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch {
    return null;
  }
}

/**
 * Checks if the stored JWT token is expired.
 * @returns {boolean} true if expired or invalid
 */
export function isTokenExpired() {
  const token = getAuthToken();
  if (!token) return true;
  const payload = decodeJWT(token);
  if (!payload || !payload.exp) return true;
  // exp is in seconds, Date.now() is in ms
  return Date.now() >= payload.exp * 1000;
}

/**
 * Gets the user_id from the stored JWT.
 * @returns {string|null}
 */
export function getUserIdFromToken() {
  const token = getAuthToken();
  if (!token) return null;
  const payload = decodeJWT(token);
  return payload?.user_id || null;
}

/**
 * Saves auth data to localStorage after login/signup.
 * @param {string} accessToken
 * @param {string} username
 */
export function saveAuthData(accessToken, username) {
  const payload = decodeJWT(accessToken);
  localStorage.setItem(CURRENT_USER_KEY, JSON.stringify({
    access_token: accessToken,
    username: username,
    user_id: payload?.user_id || null,
    provider: 'local',
    loggedInAt: new Date().toISOString(),
  }));
}

/**
 * Clears auth data and redirects to login page.
 */
export function logoutAndRedirect() {
  localStorage.removeItem(CURRENT_USER_KEY);
  window.location.href = 'login.html';
}

/**
 * Handles 401 responses globally: clear token, redirect to login.
 * @param {Response} response
 */
function handle401(response) {
  if (response.status === 401) {
    logoutAndRedirect();
    return true;
  }
  return false;
}


// ═══════════════════════════════════════════
// API REQUEST FUNCTIONS
// ═══════════════════════════════════════════

/**
 * Makes a POST request with JSON body.
 * @param {string} endpoint
 * @param {object} body
 * @param {boolean} [withAuth=false] - Include Authorization header
 * @returns {Promise<object>}
 */
async function apiPost(endpoint, body, withAuth = false) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

  try {
    const headers = { 'Content-Type': 'application/json' };

    if (withAuth) {
      const token = getAuthToken();
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      // Parse error body
      let errorBody = null;
      try {
        errorBody = await response.json();
      } catch {
        // If JSON parsing fails, try text
        try {
          const text = await response.text();
          errorBody = { detail: text };
        } catch {
          errorBody = null;
        }
      }

      // Handle 401 globally (redirect to login)
      if (response.status === 401 && withAuth) {
        handle401(response);
        throw new Error('انتهت جلستك. يرجى تسجيل الدخول مرة أخرى');
      }

      throw new Error(mapBackendError(response, errorBody));
    }

    return await response.json();
  } catch (error) {
    clearTimeout(timeoutId);

    if (error.name === 'AbortError') {
      throw new Error('انتهت مهلة الاتصال بالخادم. حاول مرة أخرى');
    }
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error('لا يمكن الاتصال بالخادم. تأكد من تشغيل الخادم على المنفذ 8000');
    }
    throw error;
  }
}

/**
 * Makes a POST request with form-encoded body (for OAuth2PasswordRequestForm).
 * @param {string} endpoint
 * @param {URLSearchParams} formData
 * @returns {Promise<object>}
 */
async function apiPostForm(endpoint, formData) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData.toString(),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      let errorBody = null;
      try {
        errorBody = await response.json();
      } catch {
        errorBody = null;
      }

      throw new Error(mapBackendError(response, errorBody));
    }

    return await response.json();
  } catch (error) {
    clearTimeout(timeoutId);

    if (error.name === 'AbortError') {
      throw new Error('انتهت مهلة الاتصال بالخادم. حاول مرة أخرى');
    }
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error('لا يمكن الاتصال بالخادم. تأكد من تشغيل الخادم على المنفذ 8000');
    }
    throw error;
  }
}


// ═══════════════════════════════════════════
// AUTH API FUNCTIONS
// ═══════════════════════════════════════════

/**
 * Logs in a user via POST /login (form-encoded for OAuth2PasswordRequestForm).
 * Returns { access_token, token_type }.
 * @param {string} username
 * @param {string} password
 * @returns {Promise<{access_token: string, token_type: string}>}
 */
export async function loginUser(username, password) {
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);

  return apiPostForm('/login', formData);
}

/**
 * Signs up a new user via POST /signup (JSON body matching UserSignup schema).
 * Returns { message, access_token }.
 * @param {{username: string, password: string, email: string, phone: string, default_address?: string}} details
 * @returns {Promise<{message: string, access_token: string}>}
 */
export async function signupUser(details) {
  return apiPost('/signup', details, false);
}


// ═══════════════════════════════════════════
// CHAT & PREDICTION API FUNCTIONS
// ═══════════════════════════════════════════

/**
 * Sends a chat message and gets the full AI prediction.
 * @param {string} text
 * @returns {Promise<object>}
 */
export async function sendMessage(text) {
  return apiPost('/final_prediction', { text }, true);
}

/**
 * Predicts intent only.
 * @param {string} text
 * @returns {Promise<object>}
 */
export async function predictIntent(text) {
  return apiPost('/predict_intent', { text }, true);
}

/**
 * Predicts sentiment only.
 * @param {string} text
 * @returns {Promise<object>}
 */
export async function predictSentiment(text) {
  return apiPost('/predict_feeling', { text }, true);
}

/**
 * Sends a chat message and handles Server-Sent Events (Streaming).
 * Includes Authorization Bearer token for the protected /chat endpoint.
 * @param {string} text
 * @param {string} userId - The user_id from the JWT
 * @param {function(string)} onTokenReceived - Callback when a new token arrives
 * @returns {Promise}
 */
export async function sendChatMessage(text, userId = '1', onTokenReceived) {
  const token = getAuthToken();
  const headers = { 'Content-Type': 'application/json' };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  console.log('[Kalemna] Sending chat message to:', `${API_BASE_URL}/chat`);
  console.log('[Kalemna] Payload:', { text, user_id: userId });

  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ text: text }),
    });

    console.log('[Kalemna] Response status:', response.status);

    if (!response.ok) {
      // Handle 401 — redirect to login
      if (response.status === 401) {
        logoutAndRedirect();
        throw new Error('انتهت جلستك. يرجى تسجيل الدخول مرة أخرى');
      }

      // Handle 429 — rate limit
      if (response.status === 429) {
        throw new Error('لقد تجاوزت الحد المسموح من الطلبات. انتظر قليلاً ثم حاول مرة أخرى');
      }

      let errorBody = null;
      try {
        errorBody = await response.json();
      } catch {
        errorBody = null;
      }

      throw new Error(mapBackendError(response, errorBody));
    }

    // Clone before any body reads — so we can fall back to .text() on the clone
    const clonedResponse = response.clone();

    // Try streaming with getReader first
    if (response.body && typeof response.body.getReader === 'function') {
      console.log('[Kalemna] Using ReadableStream for streaming...');
      try {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { value, done } = await reader.read();
          if (done) {
            // Process remaining buffer
            console.log('[Kalemna] Stream done. Remaining buffer:', JSON.stringify(buffer));
            if (buffer.trim()) {
              const lines = buffer.split('\n');
              for (const line of lines) {
                const trimmed = line.trim();
                if (trimmed.startsWith('data:')) {
                  const streamToken = trimmed.replace(/^data:\s*/, '');
                  if (streamToken && onTokenReceived) onTokenReceived(streamToken);
                } else if (trimmed.length > 0) {
                  console.log('[Kalemna] Non-SSE line in buffer:', trimmed);
                  if (onTokenReceived) onTokenReceived(trimmed);
                }
              }
            }
            console.log('[Kalemna] Stream finished successfully.');
            return;
          }

          const chunk = decoder.decode(value, { stream: true });
          console.log('[Kalemna] Raw chunk received:', JSON.stringify(chunk));
          buffer += chunk;

          let boundaryIndex;
          while ((boundaryIndex = buffer.indexOf('\n\n')) >= 0) {
            const eventStr = buffer.slice(0, boundaryIndex).trim();
            buffer = buffer.slice(boundaryIndex + 2);

            console.log('[Kalemna] Parsed event:', JSON.stringify(eventStr));
            if (eventStr.startsWith('data:')) {
              const streamToken = eventStr.replace(/^data:\s*/, '');
              if (streamToken && onTokenReceived) {
                onTokenReceived(streamToken);
              }
            } else if (eventStr.length > 0) {
              console.log('[Kalemna] Non-SSE event, treating as token:', eventStr);
              if (onTokenReceived) onTokenReceived(eventStr);
            }
          }
        }
      } catch (streamError) {
        console.warn('[Kalemna] ReadableStream failed:', streamError.message);
        console.log('[Kalemna] Falling back to text() on cloned response...');
      }
    }

    // Fallback: read the cloned response as plain text
    const fullText = await clonedResponse.text();
    console.log('[Kalemna] Full response text:', fullText);

    const lines = fullText.split('\n');
    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed.startsWith('data:')) {
        const streamToken = trimmed.replace(/^data:\s*/, '');
        if (streamToken && onTokenReceived) {
          onTokenReceived(streamToken);
        }
      }
    }
  } catch (error) {
    console.error('[Kalemna] sendChatMessage error:', error);
    console.error('[Kalemna] Error type:', error.constructor.name);
    console.error('[Kalemna] Error message:', error.message);

    if (error instanceof TypeError && error.message.toLowerCase().includes('network')) {
      throw new Error('خطأ في الاتصال بالخادم. تأكد من أن الخادم يعمل على المنفذ 8000 ويسمح بطلبات CORS');
    }
    throw error;
  }
}
