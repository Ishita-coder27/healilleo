import React, { useState, useEffect } from "react";
import PageLayout from "../components/PageLayout";
import "./MedicineSchedule.css";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";
const getToken = () => localStorage.getItem("heallio_token");

const EMPTY = { medication_name: "", dosage: "", frequency: "", start_date: "", end_date: "", notes: "", next_reminder_time: "" };

const fmt = (d) => d ? new Date(d).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" }) : "—";
const fmtTime = (dt) => {
  if (!dt) return "";
  const d = new Date(dt);
  const diff = d - new Date();
  if (diff < 0) return "Overdue";
  const h = Math.floor(diff / 36e5);
  const m = Math.floor((diff % 36e5) / 60000);
  if (h >= 24) return `In ${Math.floor(h/24)}d`;
  if (h >= 1) return `In ${h}h ${m}m`;
  if (m >= 1) return `In ${m}m`;
  return "Due now";
};

export default function MedicineSchedule() {
  const [meds,   setMeds]   = useState([]);
  const [form,   setForm]   = useState(EMPTY);
  const [saving, setSaving] = useState(false);
  const [msg,    setMsg]    = useState("");
  const [showAdd, setShowAdd] = useState(false);
  const [removing, setRemoving] = useState(null);

  const load = async () => {
    try {
      const r = await fetch(`${API}/medications/`, { headers: { Authorization: `Bearer ${getToken()}` } });
      const data = await r.json();
      setMeds(Array.isArray(data) ? data : []);
    } catch { setMeds([]); }
  };

  useEffect(() => { load(); }, []);

  const save = async () => {
    if (!form.medication_name || !form.start_date) { setMsg("Medication name and start date are required."); return; }
    setSaving(true); setMsg("");
    try {
      const r = await fetch(`${API}/medications/`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${getToken()}` },
        body: JSON.stringify(form),
      });
      const data = await r.json();
      if (r.ok) { setMsg("Medication added."); setForm(EMPTY); setShowAdd(false); load(); }
      else setMsg(data.detail || "Failed to add.");
    } catch { setMsg("Could not reach server."); }
    finally { setSaving(false); }
  };

  const remove = async (id, name) => {
    if (!window.confirm(`Remove "${name}"?`)) return;
    setRemoving(id);
    try {
      await fetch(`${API}/medications/${id}`, { method: "DELETE", headers: { Authorization: `Bearer ${getToken()}` } });
      setMeds((p) => p.filter((m) => m.id !== id));
    } catch { }
    finally { setRemoving(null); }
  };

  const upcoming = meds.filter((m) => m.next_reminder_time && new Date(m.next_reminder_time) > new Date())
    .sort((a, b) => new Date(a.next_reminder_time) - new Date(b.next_reminder_time));
  const past     = meds.filter((m) => !m.next_reminder_time || new Date(m.next_reminder_time) <= new Date());

  return (
    <PageLayout>
      <div className="med-page">

        <div className="med-header">
          <div>
            <h1 className="med-title">Medicine Reminder</h1>
            <p className="med-sub">Track medications and stay on schedule</p>
          </div>
          <button className="med-add-btn" onClick={() => { setShowAdd(true); setMsg(""); }}>
            + Add Medication
          </button>
        </div>

        {msg && <div className={`med-notice ${msg.includes("added") ? "ok" : "err"}`}>{msg}</div>}

        {/* Add form */}
        {showAdd && (
          <div className="med-form-card">
            <h2 className="med-form-title">Add Medication</h2>
            <div className="med-form-grid">
              <div className="med-field">
                <label>Medication Name <span>*</span></label>
                <input placeholder="e.g. Metformin" value={form.medication_name} onChange={(e) => setForm({ ...form, medication_name: e.target.value })} />
              </div>
              <div className="med-field">
                <label>Dosage</label>
                <input placeholder="e.g. 500mg" value={form.dosage} onChange={(e) => setForm({ ...form, dosage: e.target.value })} />
              </div>
              <div className="med-field">
                <label>Frequency</label>
                <input placeholder="e.g. Twice daily" value={form.frequency} onChange={(e) => setForm({ ...form, frequency: e.target.value })} />
              </div>
              <div className="med-field">
                <label>Next Reminder</label>
                <input type="datetime-local" value={form.next_reminder_time} onChange={(e) => setForm({ ...form, next_reminder_time: e.target.value })} />
              </div>
              <div className="med-field">
                <label>Start Date <span>*</span></label>
                <input type="date" value={form.start_date} onChange={(e) => setForm({ ...form, start_date: e.target.value })} />
              </div>
              <div className="med-field">
                <label>End Date</label>
                <input type="date" value={form.end_date} onChange={(e) => setForm({ ...form, end_date: e.target.value })} />
              </div>
              <div className="med-field med-field-full">
                <label>Notes</label>
                <textarea placeholder="e.g. Take with food, avoid grapefruit…" rows={2} value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
              </div>
            </div>
            <div className="med-form-actions">
              <button className="med-btn-save" onClick={save} disabled={saving}>{saving ? "Saving…" : "Add Medication"}</button>
              <button className="med-btn-cancel" onClick={() => { setShowAdd(false); setForm(EMPTY); setMsg(""); }}>Cancel</button>
            </div>
          </div>
        )}

        {meds.length === 0 ? (
          <div className="med-empty">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" width="48" height="48">
              <path d="M10.5 6.5l7 7m-3.5-8.5l4 4a5 5 0 01-7 7l-4-4a5 5 0 017-7z"/>
            </svg>
            <p>No medications added yet</p>
            <span>Click "Add Medication" to get started</span>
          </div>
        ) : (
          <>
            {upcoming.length > 0 && (
              <section>
                <h2 className="med-section-title">Upcoming</h2>
                <div className="med-grid">
                  {upcoming.map((m) => <MedCard key={m.id} med={m} onRemove={remove} removing={removing} fmtTime={fmtTime} fmt={fmt} highlight />)}
                </div>
              </section>
            )}
            {past.length > 0 && (
              <section>
                <h2 className="med-section-title">All Medications</h2>
                <div className="med-grid">
                  {past.map((m) => <MedCard key={m.id} med={m} onRemove={remove} removing={removing} fmtTime={fmtTime} fmt={fmt} />)}
                </div>
              </section>
            )}
          </>
        )}
      </div>
    </PageLayout>
  );
}

function MedCard({ med, onRemove, removing, fmtTime, fmt, highlight }) {
  return (
    <div className={`med-card ${highlight ? "med-card-hl" : ""}`}>
      <div className="med-card-top">
        <div className="med-card-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" width="18" height="18">
            <path d="M10.5 6.5l7 7m-3.5-8.5l4 4a5 5 0 01-7 7l-4-4a5 5 0 017-7z"/>
          </svg>
        </div>
        <div className="med-card-info">
          <div className="med-card-name">{med.medication_name}{med.dosage ? ` — ${med.dosage}` : ""}</div>
          {med.frequency && <div className="med-card-freq">{med.frequency}</div>}
        </div>
        <button className="med-remove-btn" onClick={() => onRemove(med.id, med.medication_name)} disabled={removing === med.id}>
          {removing === med.id ? "…" : (
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="14" height="14">
              <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6M10 11v6M14 11v6M9 6V4h6v2"/>
            </svg>
          )}
        </button>
      </div>
      <div className="med-card-meta">
        <span>From {fmt(med.start_date)}{med.end_date ? ` to ${fmt(med.end_date)}` : ""}</span>
        {med.next_reminder_time && (
          <span className={`med-due ${highlight ? "med-due-hl" : ""}`}>{fmtTime(med.next_reminder_time)}</span>
        )}
      </div>
      {med.notes && <p className="med-card-notes">{med.notes}</p>}
    </div>
  );
}
