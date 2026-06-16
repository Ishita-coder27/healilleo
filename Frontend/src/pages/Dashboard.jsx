import React, { useState, useRef, useEffect, useCallback } from "react";
import Sidebar from "../components/Sidebar";
import Navbar from "../components/Navbar";
import { useVoiceInput } from "../hooks/useVoiceInput";
import SuggestedCarousel from "../components/SuggestedCarousel";
import SleepTracker from "../components/SleepTracker";
import WaterTracker from "../components/WaterTracker";
import "./Dashboard.css";
import BMICalculator from "../components/BMICalculator";
import { useAuth } from "../context/AuthContext";
import ExportButton from "../components/ExportButton";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

function calcHealthScore(vitals) {
  let score = 100;
  for (const v of vitals) {
    const key = (v.key || "").toLowerCase();
    const val = parseFloat(v.value);
    if (isNaN(val)) continue;
    if (key.includes("systolic") || key === "blood_pressure_systolic") {
      if (val > 140) score -= 15; else if (val < 90) score -= 10;
    }
    if (key.includes("diastolic") || key === "blood_pressure_diastolic") {
      if (val > 90) score -= 10;
    }
    if (key.includes("heart_rate") || key === "heart_rate") {
      if (val > 100 || val < 50) score -= 10;
    }
    if (key.includes("glucose") || key.includes("blood_sugar")) {
      if (val > 126 || val > 200) score -= 15;
    }
    if (key.includes("bmi")) {
      if (val > 30 || val < 18.5) score -= 10;
    }
    if (key.includes("cholesterol")) {
      if (val > 200) score -= 10;
    }
  }
  return Math.max(0, Math.min(100, score));
}

/* ─── LLM call ─────────────────────────────────────────────── */
// async function callLLM(history) {
//   const res = await fetch("https://api.anthropic.com/v1/messages", {
//     method: "POST",
//     headers: { "Content-Type": "application/json" },
//     body: JSON.stringify({
//       model: "claude-sonnet-4-20250514",
//       max_tokens: 1000,
//       system:
//         "You are a helpful AI health assistant for Heallio. Give clear, concise, friendly health advice. Always remind users to consult a doctor for serious concerns. Keep responses under 150 words unless truly needed.",
//       messages: history.map((m) => ({
//         role: m.from === "user" ? "user" : "assistant",
//         content: m.text,
//       })),
//     }),
//   });
//   const data = await res.json();
//   return data.content?.[0]?.text || "Sorry, I couldn't get a response.";
// }

/* ═══════════════════════════════════════════════════════════
   HERO TYPING HOOK
   Sequence: type full line → blink → backspace last word →
             type next word → blink → repeat
   ═══════════════════════════════════════════════════════════ */
const HERO_BASE    = "Welcome to Heallio!\nYour personalized Health ";
const HERO_WORDS   = ["Assistant", "Coach", "Pal"];
const TYPE_SPEED   = 46;   // ms per character typed
const BACK_SPEED   = 46;   // ms per character deleted — matches type speed
const BLINK_PAUSE  = 1100; // ms of blinking before backspace starts
const WORD_PAUSE   = 1400; // ms of blinking after new word is fully typed

function useHeroTyping() {
  const [displayed,  setDisplayed]  = useState("");
  const [wordIndex,  setWordIndex]  = useState(0);
  const [phase, setPhase] = useState("typing-base"); 
  // phases: typing-base | blinking | backspacing | typing-word | word-done

  useEffect(() => {
    let timeout;

    if (phase === "typing-base") {
      // Type the base string character by character
      const full = HERO_BASE + HERO_WORDS[0];
      if (displayed.length < full.length) {
        timeout = setTimeout(() => {
          setDisplayed(full.slice(0, displayed.length + 1));
        }, TYPE_SPEED);
      } else {
        // Finished typing full first line → blink
        timeout = setTimeout(() => setPhase("blinking"), BLINK_PAUSE);
      }
    }

    else if (phase === "blinking") {
      // Just wait, CSS handles the blink, then start backspacing
      timeout = setTimeout(() => setPhase("backspacing"), BLINK_PAUSE);
    }

    else if (phase === "backspacing") {
      if (displayed.length > HERO_BASE.length) {
        timeout = setTimeout(() => {
          setDisplayed((d) => d.slice(0, -1));
        }, BACK_SPEED);
      } else {
        // Erased — advance word index then type
        setWordIndex((prev) => (prev + 1) % HERO_WORDS.length);
        setPhase("typing-word");
      }
    }

    else if (phase === "typing-word") {
      // Use wordIndex directly; React batches the setWordIndex above so by the
      // time this effect re-runs wordIndex is already the updated value.
      const targetWord = HERO_WORDS[wordIndex];
      const currentWord = displayed.slice(HERO_BASE.length);
      if (currentWord !== targetWord) {
        timeout = setTimeout(() => {
          setDisplayed(HERO_BASE + targetWord.slice(0, currentWord.length + 1));
        }, TYPE_SPEED);
      } else {
        timeout = setTimeout(() => setPhase("word-done"), WORD_PAUSE);
      }
    }

    else if (phase === "word-done") {
      // Blink briefly then backspace again
      timeout = setTimeout(() => setPhase("backspacing"), BLINK_PAUSE);
    }

    return () => clearTimeout(timeout);
  }, [phase, displayed, wordIndex]);

  const initialDone = phase !== "typing-base";
  const isCursorBlinking = phase === "blinking" || phase === "word-done";

  return { displayed, initialDone, isCursorBlinking };
}

function FullChat({
  messages,
  loading,
  onSend,    // ← receives Dashboard's sendMessage
  onBack,
  onClear
}) {
  // No useChatPipeline here — delegation happens via onSend
  const [input, setInput] = useState("");
  const [showScroll, setShowScroll] = useState(false);

  const bottomRef = useRef(null);
  const scrollRef = useRef(null);
  const inputRef = useRef(null);

  const send = async () => {
    if (!input.trim() || loading) return;
    const text = input;
    setInput("");
    await onSend(text);   // calls Dashboard's sendMessage → useChatPipeline
    inputRef.current?.focus();
  };

  /* ─────────────────────────────────────────────
     AUTO SCROLL
  ───────────────────────────────────────────── */
  useEffect(() => {
    if (!showScroll) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, loading]);

  /* ─────────────────────────────────────────────
     SCROLL DETECTION
  ───────────────────────────────────────────── */
  const handleScroll = () => {
    const el = scrollRef.current;
    if (!el) return;

    setShowScroll(
      el.scrollHeight - el.scrollTop - el.clientHeight > 120
    );
  };

  const scrollToBottom = () => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    setShowScroll(false);
  };

  const getTime = () =>
    new Date().toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit"
    });

  /* ─────────────────────────────────────────────
     SEND MESSAGE → BACKEND
  ───────────────────────────────────────────── */
  // const send = async () => {
  //   if (!input.trim() || loading) return;

  //   const userMessage = input;
  //   setInput("");

  //   // 1. Add user message
  //   setMessages((prev) => [
  //     ...prev,
  //     { from: "user", text: userMessage, time: getTime() }
  //   ]);

  //   setLoading(true);

  //   try {
  //     const answer = await processQuery(
  //       userMessage,
  //       "cardiovascular"   // temporary bucket
  //     );

  //     console.log("API RESPONSE:", data);

  //     // 2. SAFE fallback handling
  //     // const data = await res.json();

  //     setMessages((prev) => [
  //       ...prev,
  //       {
  //         from: "assistant",
  //         text: answer,
  //         time: getTime()
  //       }
  //     ]);

  //   } catch (err) {
  //     console.error(err);

  //     setMessages((prev) => [
  //       ...prev,
  //       {
  //         from: "assistant",
  //         text: "Something went wrong. Please try again.",
  //         time: getTime()
  //       }
  //     ]);
  //   } finally {
  //     setLoading(false);
  //     inputRef.current?.focus();
  //   }
  // };

  /* ─────────────────────────────────────────────
     UI
  ───────────────────────────────────────────── */
  return (
    <div className="fullchat-overlay">

      <header className="fc-topbar">
        <button className="fc-back-btn" onClick={onBack}>
          ← Back
        </button>

        <div className="fc-title">
          <div className="fc-title-avatar">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" width="18" height="18"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
          </div>
          <div>
            <div className="fc-title-name">Health Assistant</div>
            <div className="fc-title-sub">
              AI Medical Assistant · {messages.length} messages
            </div>
          </div>
        </div>

        <button className="fc-clear-btn" onClick={onClear}>
          Clear
        </button>
      </header>

      <div
        className="fc-messages"
        ref={scrollRef}
        onScroll={handleScroll}
      >
        {messages.map((msg, i) => (
          <div key={i} className={`fc-msg-row ${msg.from}`}>

            {msg.from === "assistant" && (
              <div className="fc-avatar">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" width="16" height="16"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
              </div>
            )}

            <div className={`fc-bubble ${msg.from}`}>
              <div className="fc-bubble-text">{msg.text}</div>
              <div className="fc-bubble-time">{msg.time}</div>

              {msg.buckets?.length > 0 && (
                <div className="fc-debug">
                  Buckets: {msg.buckets.join(", ")}
                </div>
              )}
            </div>

            {msg.from === "user" && (
              <div className="fc-avatar fc-avatar-user">S</div>
            )}
          </div>
        ))}

        {loading && (
          <div className="fc-msg-row assistant">
            <div className="fc-avatar">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" width="16" height="16"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
            </div>
            <div className="fc-bubble assistant">
              <div className="fc-typing">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {showScroll && (
        <button
          className="fc-scroll-btn"
          onClick={scrollToBottom}
        >
          ↓
        </button>
      )}

      <div className="fc-input-wrap">
        <div className="fc-input-bar">

          <input
            ref={inputRef}
            className="fc-ib-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send()}
            placeholder="Ask a health question..."
            disabled={loading}
          />

          <button
            className="fc-ib-send"
            onClick={send}
            disabled={loading || !input.trim()}
          >
            {loading ? "..." : "Send"}
          </button>

        </div>

        <p className="fc-disclaimer">
          AI may be inaccurate. Consult a doctor for medical advice.
        </p>
      </div>
    </div>
  );
}
/* ═══════════════════════════════════════════════════════════
   MAIN DASHBOARD
   ═══════════════════════════════════════════════════════════ */
export default function Dashboard() {
  const { user } = useAuth();
  const userId = user?.id ?? 8;

  // const { processQuery, clearContext } = useChatPipeline(userId);
  const [bmiOpen, setBmiOpen] = useState(false);  
  const [sleepTrackerOpen, setSleepTrackerOpen] = useState(false);
  const [waterTrackerOpen, setWaterTrackerOpen] = useState(false);
  const [collapsed,  setCollapsed]  = useState(false);
  const [fullscreen, setFullscreen] = useState(false);
  const [messages,   setMessages]   = useState([{
    from: "assistant",
    text: "Hi! I'm your AI Health Assistant. Ask me anything about your health.",
    time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
  }]);
  const [loading,  setLoading]  = useState(false);
  const [input,    setInput]    = useState("");
  const [focused,  setFocused]  = useState(false);

  const [healthScore, setHealthScore] = useState(null);

  // Upload state
  const [uploading, setUploading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState("");

  // Live reminder state
  const [nextAppt, setNextAppt] = useState(null);
  const [nextMed,  setNextMed]  = useState(null);

  // Tracker states (UI only)
  const [waterGlasses, setWaterGlasses] = useState(4);
  const waterGoal = 8;
  const [sleepHours, setSleepHours] = useState(6.5);
  const sleepGoal = 8;

  const inputRef     = useRef(null);
  const fileInputRef = useRef(null);

  const { listening, toggle: toggleVoice } = useVoiceInput((transcript) => {
    setInput(transcript);
  });

  // Typing animation
  const { displayed: typedHeading, initialDone: headingDone, isCursorBlinking } = useHeroTyping();

  // Fetch reminders
  useEffect(() => {
    const token = localStorage.getItem("heallio_token");
    if (!token) return;
    const fetchReminders = async () => {
      try {
        const [apptRes, medRes] = await Promise.all([
          fetch(`${API}/appointments/`, { headers: { Authorization: `Bearer ${token}` } }),
          fetch(`${API}/medications/`,  { headers: { Authorization: `Bearer ${token}` } }),
        ]);
        if (apptRes.ok) {
          const appts = await apptRes.json();
          const upcoming = appts
            .filter((a) => new Date(a.appointment_time) > new Date())
            .sort((a, b) => new Date(a.appointment_time) - new Date(b.appointment_time));
          setNextAppt(upcoming[0] || null);
        }
        if (medRes.ok) {
          const meds = await medRes.json();
          const active = meds.filter((m) => m.next_reminder_time && new Date(m.next_reminder_time) > new Date());
          active.sort((a, b) => new Date(a.next_reminder_time) - new Date(b.next_reminder_time));
          setNextMed(active[0] || null);
        }
      } catch { /* silently ignore */ }
    };
    fetchReminders();
  }, []);

  // Fetch extracted vitals for health score
  useEffect(() => {
    const token = localStorage.getItem("heallio_token");
    if (!token) return;
    fetch(`${API}/report-vitals/my-extractions?limit=5`, { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => r.ok ? r.json() : [])
      .then((data) => {
        if (!Array.isArray(data) || !data.length) return;
        // Flatten vitals_json from all extractions
        const allVitals = [];
        for (const ext of data) {
          const vj = ext.vitals_json || {};
          for (const [name, raw] of Object.entries(vj)) {
            const val = typeof raw === "string" ? parseFloat(raw.split(" ")[0]) : parseFloat(raw);
            if (!isNaN(val)) allVitals.push({ key: name.toLowerCase().replace(/\s+/g, "_"), value: val });
          }
        }
        if (allVitals.length) setHealthScore(calcHealthScore(allVitals));
      })
      .catch(() => {});
  }, []);

const sendMessage = useCallback(async (text) => {
  const msgText = (text || input).trim();
  if (!msgText || loading) return;

  setMessages(prev => [...prev, {
    from: "user",
    text: msgText,
    time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
  }]);
  setInput("");
  setLoading(true);
  setFullscreen(true);

  try {
    const token = localStorage.getItem("heallio_token");
    const r = await fetch(`${API}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ user_id: userId, message: msgText }),
    });
    const data = await r.json();
    setMessages(prev => [...prev, {
      from: "assistant",
      text: data.reply || "Sorry, I could not get a response.",
      buckets: data.buckets,
      time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    }]);
  } catch {
    setMessages(prev => [...prev, {
      from: "assistant",
      text: "Something went wrong. Please try again.",
      time: "",
    }]);
  } finally {
    setLoading(false);
  }
}, [input, loading, userId]);

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

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    if (file.type !== "application/pdf") { setUploadMsg("Only PDF files accepted."); return; }
    setUploading(true); setUploadMsg("");
    const formData = new FormData();
    formData.append("file", file);
    try {
      const token = localStorage.getItem("heallio_token");
      const res   = await fetch(`${API}/medical-reports/upload`, {
        method: "POST", headers: { Authorization: `Bearer ${token}` }, body: formData,
      });
      const data = await res.json();
      setUploadMsg(res.ok ? `"${data.file_name}" uploaded!` : (data.detail || "Upload failed."));
    } catch { setUploadMsg("Could not reach server."); }
    finally { setUploading(false); fileInputRef.current.value = ""; }
  };

  const fmtApptTime = (dt) => {
    const d = new Date(dt);
    const diffMs = d - new Date();
    const diffH  = Math.floor(diffMs / 36e5);
    const diffD  = Math.floor(diffMs / 864e5);
    if (diffD >= 1) return `In ${diffD}d`;
    if (diffH >= 1) return `In ${diffH}h`;
    return "Soon";
  };

  const fmtMedTime = (dt) => {
    const d = new Date(dt);
    const diffMs = d - new Date();
    const diffM  = Math.floor(diffMs / 60000);
    const diffH  = Math.floor(diffMs / 36e5);
    if (diffH >= 1) return `In ${diffH}h`;
    if (diffM >= 1) return `In ${diffM}m`;
    return "Now";
  };

  const waterPct  = Math.round((waterGlasses / waterGoal) * 100);
  const sleepPct  = Math.round((sleepHours / sleepGoal) * 100);

  return (
    <div className="heallio-layout">
      <Sidebar collapsed={collapsed} toggleSidebar={() => setCollapsed(!collapsed)} openBMI={() => setBmiOpen(true)} openSleepTracker={() => setSleepTrackerOpen(true)} openWaterTracker={() => setWaterTrackerOpen(true)} />

      <div className={`heallio-main ${collapsed ? "sidebar-collapsed" : ""}`}>
      <Navbar openBMI={() => setBmiOpen(true)} />

        <div className="heallio-content">

          {/* ── HERO ─────────────────────────────────────────── */}
          <section className="hero-section">
            <div className="hero-orb hero-orb-1" />
            <div className="hero-orb hero-orb-2" />
            <div className="hero-orb hero-orb-3" />

            <div className="hero-badge">
              <span className="hero-badge-dot" />
              AI Health Platform
            </div>

            <h1 className="hero-heading" style={{ whiteSpace: "pre-line" }}>
              {typedHeading}
              <span className="hero-cursor hero-cursor-blink">|</span>
            </h1>

            <p className={`hero-sub ${headingDone ? "hero-sub-visible" : ""}`}>
              I'm here to support you with any health‑related questions.<br />
              How can I help you today?
            </p>

            <div className={`hero-pills ${headingDone ? "hero-sub-visible" : ""}`}>
              <span className="hero-pill">Private &amp; Secure</span>
              <span className="hero-pill">Instant Answers</span>
              <span className="hero-pill">Medically Informed</span>
            </div>
          </section>

          {/* ── BENTO GRID ───────────────────────────────────── */}
          <section className="bento-grid">

            {/* Upload — large featured card with "+" */}
            <div className="bento-card bento-upload">
              <div className="bento-upload-bg" />
              <input ref={fileInputRef} type="file" accept=".pdf" style={{ display: "none" }} onChange={handleUpload} />
              <button
                className="bento-upload-plus"
                onClick={() => fileInputRef.current.click()}
                disabled={uploading}
                title="Upload medical report"
              >
                {uploading ? <span className="bento-spinner" /> : <span>+</span>}
              </button>
              <div className="bento-upload-text">
                <div className="bento-upload-title">Medical Reports</div>
                <div className="bento-upload-sub">
                  {uploadMsg || "Upload a PDF for AI analysis"}
                </div>
              </div>
              <div className="bento-upload-formats">PDF supported</div>
            </div>

            {/* Appointment */}
            <div className="bento-card bento-appt">
              <div className="bento-card-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" width="20" height="20"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
              </div>
              <div className="bento-card-label">Next Appointment</div>
              {nextAppt ? (
                <>
                  <div className="bento-card-value">{fmtApptTime(nextAppt.appointment_time)}</div>
                  <div className="bento-card-sub">
                    {nextAppt.doctor_name}
                    {nextAppt.clinic_name ? ` · ${nextAppt.clinic_name}` : ""}
                  </div>
                </>
              ) : (
                <>
                  <div className="bento-card-value bento-card-empty">None</div>
                  <div className="bento-card-sub">Book an appointment</div>
                </>
              )}
              <div className="bento-card-accent bento-appt-accent" />
            </div>

            {/* Medication */}
            <div className="bento-card bento-med">
              <div className="bento-card-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" width="20" height="20"><path d="M10.5 6.5l7 7m-3.5-8.5l4 4a5 5 0 01-7 7l-4-4a5 5 0 017-7z"/></svg>
              </div>
              <div className="bento-card-label">Medication Due</div>
              {nextMed ? (
                <>
                  <div className="bento-card-value">{fmtMedTime(nextMed.next_reminder_time)}</div>
                  <div className="bento-card-sub">
                    {nextMed.medication_name}
                    {nextMed.dosage ? ` · ${nextMed.dosage}` : ""}
                  </div>
                </>
              ) : (
                <>
                  <div className="bento-card-value bento-card-empty">None</div>
                  <div className="bento-card-sub">Add a medication</div>
                </>
              )}
              <div className="bento-card-accent bento-med-accent" />
            </div>

            {/* Water Tracker */}
            <div className="bento-card bento-water">
              <div className="bento-tracker-header">
                <span className="bento-card-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" width="18" height="18"><path d="M12 2C6 10 4 14 4 17a8 8 0 0016 0c0-3-2-7-8-15z"/></svg>
                </span>
                <span className="bento-card-label">Water Intake</span>
              </div>
              <div className="bento-tracker-value">{waterGlasses}<span className="bento-tracker-unit">/{waterGoal} glasses</span></div>
              <div className="bento-progress-track">
                <div className="bento-progress-fill bento-water-fill" style={{ width: `${waterPct}%` }} />
              </div>
              <div className="bento-tracker-btns">
                <button className="bento-tracker-btn" onClick={() => setWaterGlasses(Math.max(0, waterGlasses - 1))}>−</button>
                <span className="bento-tracker-pct">{waterPct}%</span>
                <button className="bento-tracker-btn bento-tracker-btn-add" onClick={() => setWaterGlasses(Math.min(waterGoal, waterGlasses + 1))}>+</button>
              </div>
            </div>

            {/* Sleep Tracker */}
            <div className="bento-card bento-sleep">
              <div className="bento-tracker-header">
                <span className="bento-card-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" width="18" height="18"><path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/></svg>
                </span>
                <span className="bento-card-label">Sleep</span>
              </div>
              <div className="bento-tracker-value">{sleepHours}<span className="bento-tracker-unit">/{sleepGoal} hrs</span></div>
              <div className="bento-progress-track">
                <div className="bento-progress-fill bento-sleep-fill" style={{ width: `${Math.min(sleepPct, 100)}%` }} />
              </div>
              <div className="bento-tracker-btns">
                <button className="bento-tracker-btn" onClick={() => setSleepHours(Math.max(0, +(sleepHours - 0.5).toFixed(1)))}>−</button>
                <span className="bento-tracker-pct">{sleepPct}%</span>
                <button className="bento-tracker-btn bento-tracker-btn-add" onClick={() => setSleepHours(Math.min(sleepGoal, +(sleepHours + 0.5).toFixed(1)))}>+</button>
              </div>
            </div>

            {/* Health Score card */}
            {healthScore !== null && (
              <div className="bento-card bento-score">
                <div className="bento-score-label">Health Score</div>
                <HealthScoreRing score={healthScore} />
                <div className="bento-score-sub">
                  {healthScore >= 80 ? "Excellent" : healthScore >= 60 ? "Good" : "Needs Attention"}
                </div>
              </div>
            )}

            {/* Export card */}
            <div className="bento-card bento-export">
              <div className="bento-card-label">Health Report</div>
              <div className="bento-export-desc">Download your vitals and medications as a PDF</div>
              <ExportButton />
            </div>

            {/* Carousel card */}
            <div className="bento-card bento-carousel">
              <SuggestedCarousel onSelect={handleSuggestedQ} />
            </div>

          </section>
        </div>
      </div>

      {fullscreen && (
        <FullChat
          messages={messages}
          setMessages={setMessages}
          loading={loading}
          setLoading={setLoading}
          onSend={sendMessage}
          onBack={() => setFullscreen(false)}
          onClear={clearChat}
        />
      )}

      {!fullscreen && (
        <div className={`floating-input-wrap ${focused ? "focused" : ""} ${collapsed ? "sidebar-collapsed" : ""}`}>
          <div className="floating-input-bar">
            <button className="fib-icon-btn fib-attach" title="Attach file">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
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
            <button
              className={`fib-icon-btn fib-mic ${listening ? "fib-mic-active" : ""}`}
              title={listening ? "Stop listening" : "Voice input"}
              onClick={toggleVoice}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="9" y="2" width="6" height="11" rx="3"/>
                <path d="M5 10a7 7 0 0 0 14 0"/>
                <line x1="12" y1="19" x2="12" y2="22"/>
                <line x1="9" y1="22" x2="15" y2="22"/>
              </svg>
            </button>
            <button className={`fib-send-btn ${input.trim() ? "active" : ""}`} onClick={() => sendMessage()} disabled={!input.trim()}>
              <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 4l8 8-8 8V4z"/></svg>
            </button>
          </div>
          <p className="fib-disclaimer">Heallio AI may make mistakes. Always consult a qualified healthcare professional.</p>
        </div>
      )}
      <SleepTracker open={sleepTrackerOpen} onClose={() => setSleepTrackerOpen(false)} onAskLLM={(q) => { setSleepTrackerOpen(false); handleSuggestedQ(q); }}/>
      <WaterTracker open={waterTrackerOpen} onClose={() => setWaterTrackerOpen(false)} onAskLLM={(q) => { setWaterTrackerOpen(false); handleSuggestedQ(q); }}/>
      <BMICalculator open={bmiOpen} onClose={()=>setBmiOpen(false)} />
    </div>
  );
}

function HealthScoreRing({ score }) {
  const r = 36, cx = 44, cy = 44;
  const circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;
  const color = score >= 80 ? "#10B981" : score >= 60 ? "#F59E0B" : "#EF4444";
  return (
    <svg width="88" height="88" viewBox="0 0 88 88" style={{ display: "block", margin: "8px auto 4px" }}>
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="var(--border)" strokeWidth="8" />
      <circle cx={cx} cy={cy} r={r} fill="none" stroke={color} strokeWidth="8"
        strokeDasharray={circ} strokeDashoffset={offset}
        strokeLinecap="round" transform={`rotate(-90 ${cx} ${cy})`}
        style={{ transition: "stroke-dashoffset 0.8s ease" }}
      />
      <text x={cx} y={cy + 6} textAnchor="middle" fontSize="18" fontWeight="700" fill="var(--text)">{score}</text>
    </svg>
  );
}
