const API_URL  = process.env.REACT_APP_API_URL  || "http://localhost:8000";
const API_BASE = process.env.REACT_APP_API_BASE || "/api/v1";

export async function sendChatMessage(message) {
  const r = await fetch(`${API_URL}${API_BASE}/assistant/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

export async function getAssistantStatus() {
  const r = await fetch(`${API_URL}${API_BASE}/assistant/status`);
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}
