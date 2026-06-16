import React, { useState, useEffect, useRef } from "react";
import PageLayout from "../components/PageLayout";
import BMICalculator from "../components/BMICalculator";
import ReactMarkdown from "react-markdown";
import "./MedicalReports.css";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";
const getToken = () => localStorage.getItem("heallio_token");

const fmt = (d) =>
  new Date(d).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });

export default function MedicalReports() {
  const [reports,   setReports]   = useState([]);
  const [uploading, setUploading] = useState(false);
  const [deleting,  setDeleting]  = useState(null);
  const [msg,       setMsg]       = useState("");
  const [selected,  setSelected]  = useState(null);

  // chat
  const [chatHistory, setChatHistory] = useState([]);
  const [chatInput,   setChatInput]   = useState("");
  const [chatting,    setChatting]    = useState(false);

  const [bmiOpen,   setBmiOpen]   = useState(false);
  const fileRef = useRef(null);
  const chatBottomRef = useRef(null);

  const load = async () => {
    try {
      const r = await fetch(`${API}/medical-reports/`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      const data = await r.json();
      setReports(Array.isArray(data) ? data : []);
    } catch { setReports([]); }
  };

  useEffect(() => { load(); }, []);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory, chatting]);

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    if (file.type !== "application/pdf") { setMsg("Only PDF files are accepted."); return; }
    setUploading(true); setMsg("");
    const fd = new FormData();
    fd.append("file", file);
    try {
      const r = await fetch(`${API}/medical-reports/upload`, {
        method: "POST",
        headers: { Authorization: `Bearer ${getToken()}` },
        body: fd,
      });
      const data = await r.json();
      setMsg(r.ok ? `"${data.file_name}" uploaded successfully.` : (data.detail || "Upload failed."));
      if (r.ok) load();
    } catch { setMsg("Could not reach server."); }
    finally { setUploading(false); fileRef.current.value = ""; }
  };

  const handleOpen = async (id) => {
    try {
      const r = await fetch(`${API}/medical-reports/download/${id}`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (!r.ok) { setMsg("Could not open file."); return; }
      const blob = await r.blob();
      window.open(URL.createObjectURL(blob), "_blank");
    } catch { setMsg("Could not reach server."); }
  };

  const handleDelete = async (id, name) => {
    if (!window.confirm(`Delete "${name}"?`)) return;
    setDeleting(id);
    try {
      const r = await fetch(`${API}/medical-reports/delete/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (r.ok) { setReports((p) => p.filter((x) => x.id !== id)); if (selected?.id === id) setSelected(null); }
      else setMsg("Delete failed.");
    } catch { setMsg("Could not reach server."); }
    finally { setDeleting(null); }
  };

  const sendChat = async () => {
    const text = chatInput.trim();
    if (!text || chatting) return;
    setChatInput("");
    const userMsg = { role: "user", text, time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) };
    setChatHistory((p) => [...p, userMsg]);
    setChatting(true);
    try {
      const storedUser = JSON.parse(localStorage.getItem("heallio_user") || "{}");
      const userId = storedUser.id ?? 1;
      const r = await fetch(`${API}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${getToken()}` },
        body: JSON.stringify({ user_id: userId, message: text }),
      });
      const data = await r.json();
      setChatHistory((p) => [...p, {
        role: "assistant",
        text: data.reply || "I couldn't get a response. Please try again.",
        time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      }]);
    } catch {
      setChatHistory((p) => [...p, { role: "assistant", text: "Something went wrong.", time: "" }]);
    } finally { setChatting(false); }
  };

  return (
    <PageLayout onBMI={() => setBmiOpen(true)}>
      <div className="mr-page">

        {/* ── Header ── */}
        <div className="mr-header">
          <div>
            <h1 className="mr-title">Medical Reports</h1>
            <p className="mr-sub">Upload, manage, and analyse your lab reports with AI</p>
          </div>
          <button className="mr-upload-btn" onClick={() => fileRef.current.click()} disabled={uploading}>
            {uploading ? <span className="mr-spinner" /> : (
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12"/></svg>
            )}
            {uploading ? "Uploading…" : "Upload PDF"}
          </button>
          <input ref={fileRef} type="file" accept=".pdf" style={{ display: "none" }} onChange={handleUpload} />
        </div>

        {msg && (
          <div className={`mr-notice ${msg.includes("success") ? "mr-notice-ok" : "mr-notice-err"}`}>
            {msg}
            <button onClick={() => setMsg("")} className="mr-notice-close">×</button>
          </div>
        )}

        <div className="mr-body">
          {/* ── Reports list ── */}
          <div className="mr-list-col">
            <h2 className="mr-col-title">Your Reports</h2>
            {reports.length === 0 ? (
              <div className="mr-empty">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" width="48" height="48"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8L14 2zm0 0v6h6"/></svg>
                <p>No reports yet</p>
                <span>Upload your first PDF to get started</span>
              </div>
            ) : (
              <ul className="mr-list">
                {reports.map((r) => (
                  <li
                    key={r.id}
                    className={`mr-item ${selected?.id === r.id ? "mr-item-selected" : ""}`}
                    onClick={() => setSelected(r)}
                  >
                    <div className="mr-item-icon">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" width="20" height="20"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8L14 2zm0 0v6h6M9 13h6M9 17h4"/></svg>
                    </div>
                    <div className="mr-item-info">
                      <div className="mr-item-name">{r.file_name}</div>
                      <div className="mr-item-date">{fmt(r.uploaded_at)}</div>
                    </div>
                    <span className={`mr-badge ${r.processed ? "mr-badge-done" : "mr-badge-pending"}`}>
                      {r.processed ? "Processed" : "Pending"}
                    </span>
                    <div className="mr-item-actions">
                      <button className="mr-action-btn" onClick={(e) => { e.stopPropagation(); handleOpen(r.id); }} title="Open PDF">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="14" height="14"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                      </button>
                      <button className="mr-action-btn mr-action-del" onClick={(e) => { e.stopPropagation(); handleDelete(r.id, r.file_name); }} disabled={deleting === r.id} title="Delete">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="14" height="14"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6M10 11v6M14 11v6M9 6V4h6v2"/></svg>
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* ── AI Chat panel ── */}
          <div className="mr-chat-col">
            <h2 className="mr-col-title">AI Health Assistant</h2>
            <p className="mr-chat-hint">Ask about your vitals, medications, or general health questions</p>

            <div className="mr-chat-messages">
              {chatHistory.length === 0 && (
                <div className="mr-chat-empty">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" width="40" height="40"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>
                  <p>Ask a health question to get started</p>
                </div>
              )}
              {chatHistory.map((msg, i) => (
                <div key={i} className={`mr-msg ${msg.role}`}>
                  <div className="mr-bubble">
                    <ReactMarkdown>{msg.text}</ReactMarkdown>
                  </div>
                  <span className="mr-msg-time">{msg.time}</span>
                </div>
              ))}
              {chatting && (
                <div className="mr-msg assistant">
                  <div className="mr-bubble mr-typing">
                    <span /><span /><span />
                  </div>
                </div>
              )}
              <div ref={chatBottomRef} />
            </div>

            <div className="mr-chat-input">
              <input
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendChat()}
                placeholder="Ask about your health or reports…"
                disabled={chatting}
              />
              <button onClick={sendChat} disabled={chatting || !chatInput.trim()}>
                <svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16"><path d="M22 2L11 13M22 2L15 22 11 13 2 9l20-7z"/></svg>
              </button>
            </div>
            <p className="mr-disclaimer">AI may be inaccurate. Always consult a qualified healthcare professional.</p>
          </div>
        </div>
      </div>
      <BMICalculator open={bmiOpen} onClose={() => setBmiOpen(false)} />
    </PageLayout>
  );
}
