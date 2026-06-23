const api = window.location.origin;
const sessionButton = document.getElementById('sessionButton');
const validateButton = document.getElementById('validateButton');
const sessionOut = document.getElementById('sessionOut');
const validateOut = document.getElementById('validateOut');
const sessionIdInput = document.getElementById('sessionId');
const cpfInput = document.getElementById('cpf');
const issuerStateInput = document.getElementById('issuerState');

async function readResponse(response) {
  const payload = await response.json().catch(() => ({ error: 'INVALID_JSON_RESPONSE' }));
  if (!response.ok && !payload.reason && !payload.error) {
    payload.error = `HTTP_${response.status}`;
  }
  return payload;
}

sessionButton.addEventListener('click', async () => {
  sessionButton.disabled = true;
  try {
    const response = await fetch(`${api}/api/session/start`, { method: 'POST' });
    const payload = await readResponse(response);
    if (!response.ok) throw new Error(payload.reason || payload.error || 'SESSION_START_FAILED');

    sessionIdInput.value = payload.sessionId;
    sessionOut.textContent = JSON.stringify(payload, null, 2);
  } catch (error) {
    sessionOut.textContent = JSON.stringify({ gate: 'HOLD', reason: error.message }, null, 2);
  } finally {
    sessionButton.disabled = false;
  }
});

validateButton.addEventListener('click', async () => {
  validateButton.disabled = true;
  const payload = {
    sessionId: sessionIdInput.value.trim(),
    cpf: cpfInput.value,
    issuerState: issuerStateInput.value.trim().toUpperCase()
  };

  try {
    const response = await fetch(`${api}/api/cin/validate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const responsePayload = await readResponse(response);
    validateOut.textContent = JSON.stringify(responsePayload, null, 2);
  } catch (error) {
    validateOut.textContent = JSON.stringify({ gate: 'HOLD', reason: error.message }, null, 2);
  } finally {
    cpfInput.value = '';
    validateButton.disabled = false;
  }
});
