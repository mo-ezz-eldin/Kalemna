/* ============================================
   Kalemna — API Client (api.js)
   كلمنا — عميل الواجهة البرمجية
   ============================================ */

const API_BASE_URL = 'http://localhost:8000';
const REQUEST_TIMEOUT = 600000;

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
/**
 * Sends a chat message and handles Server-Sent Events (Streaming).
 * @param {string} text
 * @param {string} userId
 * @param {function(string)} onTokenReceived - Callback when a new token arrives
 * @returns {Promise}
 */
export async function sendChatMessage(text, userId = "1", onTokenReceived) {
  console.log('[Kalemna] Sending chat message to:', `${API_BASE_URL}/chat`);
  console.log('[Kalemna] Payload:', { text, user_id: userId });

  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: text, user_id: userId }),
    });

    console.log('[Kalemna] Response status:', response.status);

    if (!response.ok) {
      const errorBody = await response.text().catch(() => '');
      throw new Error(`خطأ في الخادم (${response.status}): ${errorBody}`);
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
                  const token = trimmed.replace(/^data:\s*/, '');
                  if (token && onTokenReceived) onTokenReceived(token);
                } else if (trimmed.length > 0) {
                  // Non-SSE content — treat as raw token
                  console.log('[Kalemna] Non-SSE line in buffer:', trimmed);
                  if (onTokenReceived) onTokenReceived(trimmed);
                }
              }
            }
            console.log('[Kalemna] Stream finished successfully.');
            return; // Done — no fallback needed
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
              const token = eventStr.replace(/^data:\s*/, '');
              if (token && onTokenReceived) {
                onTokenReceived(token);
              }
            } else if (eventStr.length > 0) {
              // Non-SSE content — treat as raw token
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
        const token = trimmed.replace(/^data:\s*/, '');
        if (token && onTokenReceived) {
          onTokenReceived(token);
        }
      }
    }
  } catch (error) {
    console.error('[Kalemna] sendChatMessage error:', error);
    console.error('[Kalemna] Error type:', error.constructor.name);
    console.error('[Kalemna] Error message:', error.message);

    if (error instanceof TypeError && error.message.toLowerCase().includes('network')) {
      throw new Error('خطأ في الاتصال بالخادم. تأكد من أن الخادم يعمل على المنفذ 8000 ويسمح بطلبات CORS.');
    }
    throw error;
  }
}

