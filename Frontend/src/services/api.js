// src/services/api.js

const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

/**
 * Main chat call — sends query, user_id, and optional context summary.
 * Backend handles classification, DB fetch, LLM call.
 */
export async function sendChatMessage({ userId, message, contextSummary = null }) {
  const res = await fetch(`${BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: userId,
      message,
      context_summary: contextSummary,
    }),
  });

  if (!res.ok) throw new Error(`Chat API error: ${res.status}`);
  return await res.json();
  // Returns: { reply, vitals, buckets, summary, cached_vitals_used }
}

/**
 * Clear the backend session context for this user.
 */
export async function clearChatSession(userId) {
  const res = await fetch(`${BASE}/chat/clear`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId }),
  });
  if (!res.ok) throw new Error(`Clear session error: ${res.status}`);
  return await res.json();
}