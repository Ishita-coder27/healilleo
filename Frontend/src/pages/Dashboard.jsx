import React, { useState, useRef, useEffect, useCallback } from "react";
import Sidebar from "../components/Sidebar";
import Navbar from "../components/Navbar";
import "./Dashboard.css";

const SUGGESTED_QUESTIONS = [
  { icon: "🩺", text: "What do my recent blood test results mean?" },
  { icon: "💊", text: "Are there side effects to my current medications?" },
  { icon: "😴", text: "How can I improve my sleep quality?" },
  { icon: "🍎", text: "What diet changes help with high blood pressure?" },
  { icon: "🏃", text: "How much exercise should I do per week?" },
  { icon: "🤒", text: "I have a persistent headache — what could it be?" },
];

/* ─── LLM call ───────────────────────────────────────────── */
async function callLLM(history) {
  const res = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: "claude-sonnet-4-20250514",
      max_tokens: 1000,
      system:
        "You are a helpful AI health assistant for Heallio. Give clear, concise, friendly health advice. Always remind users to consult a doctor for serious concerns. Keep responses under 150 words unless truly needed.",
      messages: history.map((m) => ({
        role: m.from === "user" ? "user" : "assistant",
        content: m.text,
      })),
    }),
  });
  const data = await res.json();
  return data.content?.[0]?.text || "Sorry, I couldn't get a response.";
}

/* ═══════════════════════════════════════════════════════════
   FULL-SCREEN CHAT VIEW
   ═══════════════════════════════════════════════════════════ */
function FullChat({ messages, loading, onSend, onBack, onClear }) {
  const [input, setInput]           = useState("");
  const [showScroll, setShowScroll] = useState(false);
  const bottomRef                   = useRef(null);
  const scrollRef                   = useRef(null);
  const inputRef                    = useRef(null);

  /* auto-scroll on new message */
  useEffect(() => {
    if (!showScroll) bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  /* show/hide scroll button */
  const handleScroll = () => {
    const el = scrollRef.current;
    if (!el) return;
    setShowScroll(el.scrollHeight - el.scrollTop - el.clientHeight > 120);
  };

  const scrollToBottom = () => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    setShowScroll(false);
  };

  const send = () => {
    if (!input.trim() || loading) return;
    onSend(input);
    setInput("");
    inputRef.current?.focus();
  };

  return (
    <div className="fullchat-overlay">
      {/* ── Top bar ── */}
      <header className="fc-topbar">
        <button className="fc-back-btn" onClick={onBack} title="Back">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2"
            strokeLinecap="round" strokeLinejoin="round">
            <path d="M19 12H5M12 5l-7 7 7 7"/>
          </svg>
          <span>Back</span>
        </button>

        <div className="fc-title">
          <div className="fc-title-avatar">🩺</div>
          <div>
            <div className="fc-title-name">Health Assistant</div>
            <div className="fc-title-sub">Powered by Claude AI · {messages.length} messages</div>
          </div>
        </div>

        <button className="fc-clear-btn" onClick={onClear} title="Clear chat">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
            strokeLinecap="round" strokeLinejoin="round">
            <polyline points="3 6 5 6 21 6"/>
            <path d="M19 6l-1 14H6L5 6"/>
            <path d="M10 11v6M14 11v6"/>
            <path d="M9 6V4h6v2"/>
          </svg>
          <span>Clear</span>
        </button>
      </header>

      {/* ── Messages ── */}
      <div className="fc-messages" ref={scrollRef} onScroll={handleScroll}>
        {messages.map((msg, i) => (
          <div key={i} className={`fc-msg-row ${msg.from}`}>
            {msg.from === "assistant" && (
              <div className="fc-avatar">🩺</div>
            )}
            <div className={`fc-bubble ${msg.from}`}>
              <div className="fc-bubble-text">{msg.text}</div>
              <div className="fc-bubble-time">
                {msg.time || new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
              </div>
            </div>
            {msg.from === "user" && (
              <div className="fc-avatar fc-avatar-user">S</div>
            )}
          </div>
        ))}

        {loading && (
          <div className="fc-msg-row assistant">
            <div className="fc-avatar">🩺</div>
            <div className="fc-bubble assistant">
              <div className="fc-typing">
                <span /><span /><span />
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Scroll-to-bottom fab */}
      {showScroll && (
        <button className="fc-scroll-btn" onClick={scrollToBottom} title="Scroll to latest">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"
            strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 5v14M5 12l7 7 7-7"/>
          </svg>
        </button>
      )}

      {/* ── Bottom input ── */}
      <div className="fc-input-wrap">
        <div className="fc-input-bar">
          <button className="fc-ib-btn" title="Attach">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
              strokeLinecap="round" strokeLinejoin="round">
              <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
          </button>

          <input
            ref={inputRef}
            className="fc-ib-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
            placeholder="Ask a health question…"
            disabled={loading}
            autoFocus
          />

          <button className="fc-ib-btn" title="Voice">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
              strokeLinecap="round" strokeLinejoin="round">
              <rect x="9" y="2" width="6" height="11" rx="3"/>
              <path d="M5 10a7 7 0 0 0 14 0"/>
              <line x1="12" y1="19" x2="12" y2="22"/>
              <line x1="9" y1="22" x2="15" y2="22"/>
            </svg>
          </button>

          <button
            className={`fc-ib-send ${input.trim() && !loading ? "active" : ""}`}
            onClick={send}
            disabled={loading || !input.trim()}
          >
            {loading ? (
              <span className="fc-spinner" />
            ) : (
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 4l8 8-8 8V4z"/>
              </svg>
            )}
          </button>
        </div>
        <p className="fc-disclaimer">
          Heallio AI may make mistakes. Always consult a qualified healthcare professional.
        </p>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════
   MAIN DASHBOARD
   ═══════════════════════════════════════════════════════════ */
export default function Dashboard() {
  const [collapsed,  setCollapsed]  = useState(false);
  const [fullscreen, setFullscreen] = useState(false);
  const [messages,   setMessages]   = useState([
    {
      from: "assistant",
      text: "Hi! I'm your AI Health Assistant. Ask me anything about your health 🩺",
      time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    },
  ]);
  const [loading,  setLoading]  = useState(false);
  const [input,    setInput]    = useState("");
  const [focused,  setFocused]  = useState(false);
  const inputRef                = useRef(null);

  const sendMessage = useCallback(async (text) => {
    const msgText = (text || input).trim();
    if (!msgText || loading) return;

    const userMsg = {
      from: "user",
      text: msgText,
      time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };
    const updated = [...messages, userMsg];
    setMessages(updated);
    setInput("");
    setLoading(true);
    setFullscreen(true);   // ← open full-screen on send

    try {
      const reply = await callLLM(updated);
      setMessages((prev) => [
        ...prev,
        {
          from: "assistant",
          text: reply,
          time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { from: "assistant", text: "Something went wrong. Please try again.", time: "" },
      ]);
    } finally {
      setLoading(false);
    }
  }, [input, messages, loading]);

  const handleSuggestedQ = (q) => {
    setInput(q);
    setTimeout(() => sendMessage(q), 50);
  };

  const clearChat = () => {
    setMessages([{
      from: "assistant",
      text: "Chat cleared. How can I help you?",
      time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    }]);
  };

  return (
    <div className="heallio-layout">
      <Sidebar collapsed={collapsed} toggleSidebar={() => setCollapsed(!collapsed)} />

      <div className={`heallio-main ${collapsed ? "sidebar-collapsed" : ""}`}>
        <Navbar />

        <div className="heallio-content">
          {/* Intro */}
          <div className="assistant-intro">
            <div className="assistant-avatar-lg">🩺</div>
            <h1>Hi! I'm your AI Health Assistant</h1>
            <p>I'm here to support you with any health‑related questions.<br />How can I help you today?</p>
          </div>

          {/* Upload CTA */}
          <div className="upload-cta">
            <div className="upload-inner">
              <span className="upload-icon">📁</span>
              <div className="upload-text">
                <div className="upload-title">Upload a Medical Report</div>
                <div className="upload-sub">Get instant AI‑powered interpretation of your lab results</div>
              </div>
              <button className="upload-btn">Upload Report →</button>
            </div>
          </div>

          {/* Reminders */}
          <div className="reminders-row">
            <div className="reminder-card reminder-appt">
              <div className="reminder-icon">🗓️</div>
              <div>
                <div className="reminder-title">Next Appointment</div>
                <div className="reminder-val">Tomorrow, 10:00 AM</div>
                <div className="reminder-sub">Dr. Sharma — General Checkup</div>
              </div>
            </div>
            <div className="reminder-card reminder-med">
              <div className="reminder-icon">💊</div>
              <div>
                <div className="reminder-title">Medication Due</div>
                <div className="reminder-val">In 3 hours</div>
                <div className="reminder-sub">Metformin 500mg — with meal</div>
              </div>
            </div>
          </div>

          {/* Suggested questions */}
          <div className="suggested-section">
            <p className="suggested-label">Try asking…</p>
            <div className="suggested-grid">
              {SUGGESTED_QUESTIONS.map((q, i) => (
                <button className="suggested-chip" key={i} onClick={() => handleSuggestedQ(q.text)}>
                  <span className="chip-icon">{q.icon}</span>
                  <span>{q.text}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ── Full-screen chat (conditionally rendered) ── */}
      {fullscreen && (
        <FullChat
          messages={messages}
          loading={loading}
          onSend={sendMessage}
          onBack={() => setFullscreen(false)}
          onClear={clearChat}
        />
      )}

      {/* ── Floating input bar (always visible when not fullscreen) ── */}
      {!fullscreen && (
        <div className={`floating-input-wrap ${focused ? "focused" : ""} ${collapsed ? "sidebar-collapsed" : ""}`}>
          <div className="floating-input-bar">
            <button className="fib-icon-btn fib-attach" title="Attach file">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
                strokeLinecap="round" strokeLinejoin="round">
                <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
              </svg>
            </button>

            <input
              ref={inputRef}
              className="fib-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
              onFocus={() => setFocused(true)}
              onBlur={() => setFocused(false)}
              placeholder="Ask anything about your health…"
            />

            <button className="fib-icon-btn fib-mic" title="Voice input">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
                strokeLinecap="round" strokeLinejoin="round">
                <rect x="9" y="2" width="6" height="11" rx="3"/>
                <path d="M5 10a7 7 0 0 0 14 0"/>
                <line x1="12" y1="19" x2="12" y2="22"/>
                <line x1="9" y1="22" x2="15" y2="22"/>
              </svg>
            </button>

            <button
              className={`fib-send-btn ${input.trim() ? "active" : ""}`}
              onClick={() => sendMessage()}
              disabled={!input.trim()}
            >
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 4l8 8-8 8V4z"/>
              </svg>
            </button>
          </div>
          <p className="fib-disclaimer">
            Heallio AI may make mistakes. Always consult a qualified healthcare professional.
          </p>
        </div>
      )}
    </div>
  );
}