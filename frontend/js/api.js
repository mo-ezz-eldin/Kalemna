/* ============================================
   Kalemna — API Client (api.js)
   كلمنا — عميل الواجهة البرمجية
   ============================================ */

const API_BASE_URL = 'http://localhost:8000';
const REQUEST_TIMEOUT = 15000; // 15 seconds

/**
 * Makes a POST request to the API.
 * @param {string} endpoint
 * @param {object} body
 * @returns {Promise<object>}
 */
async function apiPost(endpoint, body) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorText = await response.text().catch(() => '');
      throw new Error(`خطأ في الخادم (${response.status}): ${errorText || 'حدث خطأ غير متوقع'}`);
    }

    return await response.json();
  } catch (error) {
    clearTimeout(timeoutId);

    if (error.name === 'AbortError') {
      throw new Error('انتهت مهلة الاتصال بالخادم. حاول مرة أخرى.');
    }
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error('لا يمكن الاتصال بالخادم. تأكد من تشغيل الخادم على المنفذ 8000.');
    }
    throw error;
  }
}

/**
 * Sends a chat message and gets the full AI prediction.
 * @param {string} text
 * @returns {Promise<object>}
 */
export async function sendMessage(text) {
  return apiPost('/final_prediction', { text });
}

/**
 * Predicts intent only.
 * @param {string} text
 * @returns {Promise<object>}
 */
export async function predictIntent(text) {
  return apiPost('/predict_intent', { text });
}

/**
 * Predicts sentiment only.
 * @param {string} text
 * @returns {Promise<object>}
 */
export async function predictSentiment(text) {
  return apiPost('/predict_feeling', { text });
}
