import React, { useState } from "react";
import "./ExportButton.css";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function ExportButton({ variant = "default" }) {
  const [loading, setLoading] = useState(false);
  const [msg,     setMsg]     = useState("");

  const download = async () => {
    setLoading(true); setMsg("");
    try {
      const token = localStorage.getItem("heallio_token");
      const r = await fetch(`${API}/export/health-report`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!r.ok) { setMsg("Export failed. Please try again."); return; }
      const blob = await r.blob();
      const url  = URL.createObjectURL(blob);
      const a    = document.createElement("a");
      a.href     = url;
      a.download = `heallio-report-${new Date().toISOString().slice(0,10)}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      setMsg("Downloaded!");
    } catch { setMsg("Could not reach server."); }
    finally { setLoading(false); setTimeout(() => setMsg(""), 3000); }
  };

  return (
    <div className={`export-wrap ${variant}`}>
      <button className="export-btn" onClick={download} disabled={loading}>
        {loading ? (
          <><span className="export-spin" /> Generating PDF…</>
        ) : (
          <>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="15" height="15">
              <path d="M12 3v13M5 14l7 7 7-7"/><line x1="3" y1="21" x2="21" y2="21"/>
            </svg>
            Export Health Report
          </>
        )}
      </button>
      {msg && <span className={`export-msg ${msg.includes("Downloaded") ? "ok" : "err"}`}>{msg}</span>}
    </div>
  );
}
