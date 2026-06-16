import React, { useState, useRef, useEffect, useCallback } from "react";
import PageLayout from "../components/PageLayout";
import ReactMarkdown from "react-markdown";
import { useVoiceInput } from "../hooks/useVoiceInput";
import "./AIAssistant.css";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";
const getToken = () => localStorage.getItem("heallio_token");

const STARTERS = [
  "What do my recent vitals indicate?",
  "Suggest a diet plan for better heart health",
  "How much water should I drink daily?",
  "What exercises are safe for high blood pressure?",
];

export default function AIAssistant() {
  const [messages, setMessages] = useState([{
    role: "assistant",
    text: "Hello! I'm your AI health assistant. I can answer questions about your health, explain your vitals, and suggest lifestyle improvements. How can I help you today?",
    time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
  }]);
  const [input,    setInput]    = useState("");
  const [loading,  setLoading]  = useState(false);
  const [summary,  setSummary]  = useState(null);

  const bottomRef = useRef(null);
  const inputRef  = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const send = useCallback(async (text) => {
    const msg = (text || input).trim();
    if (!msg || loading) return;
    setInput("");
    const time = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    setMessages((p) => [...p, { role: "user", text: msg, time }]);
    setLoading(true);
    try {
      const storedUser = JSON.parse(localStorage.getItem("heallio_user") || "{}");
      const r = await fetch(`${API}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${getToken()}` },
        body: JSON.stringify({ user_id: storedUser.id ?? 1, message: msg, context_summary: summary }),
      });
      const data = await r.json();
      if (data.summary) setSummary(data.summary);
      setMessages((p) => [...p, {
        role: "assistant",
        text: data.reply || "I couldn't get a response. Please try again.",
        time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      }]);
    } catch {
      setMessages((p) => [...p, { role: "assistant", text: "Something went wrong. Please try again.", time: "" }]);
    } finally { setLoading(false); inputRef.current?.focus(); }
  }, [input, loading, summary]);

  const { listening, toggle: toggleVoice } = useVoiceInput((t) => { setInput(t); });

  const clearChat = () => {
    setMessages([{ role: "assistant", text: "Chat cleared. How can I help you?", time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) }]);
    setSummary(null);
  };

  return (
    <PageLayout>
      <div className="ai-page">
        <div className="ai-header">
          <div>
            <h1 className="ai-title">AI Health Assistant</h1>
            <p className="ai-sub">Powered by Groq — your personal health advisor</p>
          </div>
          <button className="ai-clear-btn" onClick={clearChat}>Clear chat</button>
        </div>

        {/* Starter chips */}
        {messages.length === 1 && (
          <div className="ai-starters">
            {STARTERS.map((q) => (
              <button key={q} className="ai-starter-chip" onClick={() => send(q)}>{q}</button>
            ))}
          </div>
        )}

        <div className="ai-messages">
          {messages.map((m, i) => (
            <div key={i} className={`ai-msg ${m.role}`}>
              {m.role === "assistant" && (
                <div className="ai-avatar">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" width="16" height="16">
                    <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
                  </svg>
                </div>
              )}
              <div className="ai-bubble-wrap">
                <div className="ai-bubble">
                  <ReactMarkdown>{m.text}</ReactMarkdown>
                </div>
                {m.time && <span className="ai-time">{m.time}</span>}
              </div>
            </div>
          ))}
          {loading && (
            <div className="ai-msg assistant">
              <div className="ai-avatar">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" width="16" height="16">
                  <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
                </svg>
              </div>
              <div className="ai-bubble ai-typing">
                <span /><span /><span />
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <div className="ai-input-area">
          <div className="ai-input-bar">
            <input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
              placeholder="Ask a health question…"
              disabled={loading}
              autoFocus
            />
            <button
              className={`ai-mic-btn ${listening ? "active" : ""}`}
              onClick={toggleVoice}
              title={listening ? "Stop" : "Voice input"}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
                <rect x="9" y="2" width="6" height="11" rx="3"/>
                <path d="M5 10a7 7 0 0014 0"/>
                <line x1="12" y1="19" x2="12" y2="22"/>
                <line x1="9" y1="22" x2="15" y2="22"/>
              </svg>
            </button>
            <button className="ai-send-btn" onClick={() => send()} disabled={loading || !input.trim()}>
              <svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16">
                <path d="M22 2L11 13M22 2L15 22 11 13 2 9l20-7z"/>
              </svg>
            </button>
          </div>
          <p className="ai-disclaimer">AI may be inaccurate. Always consult a qualified healthcare professional.</p>
        </div>
      </div>
    </PageLayout>
  );
}
