import React, { useState, useEffect } from "react";
import PageLayout from "../components/PageLayout";
import "./Appointments.css";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";
const getToken = () => localStorage.getItem("heallio_token");

const EMPTY = { doctor_name: "", clinic_name: "", appointment_time: "", notes: "" };

const fmtDT = (dt) => {
  if (!dt) return "—";
  const d = new Date(dt);
  return d.toLocaleDateString("en-IN", { weekday: "short", day: "numeric", month: "short", year: "numeric" })
    + " · " + d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
};

const relTime = (dt) => {
  if (!dt) return "";
  const diff = new Date(dt) - new Date();
  if (diff < 0) return "Past";
  const h = Math.floor(diff / 36e5);
  const d = Math.floor(h / 24);
  if (d >= 1) return `In ${d} day${d > 1 ? "s" : ""}`;
  if (h >= 1) return `In ${h}h`;
  return "Today";
};

export default function Appointments() {
  const [appts,    setAppts]   = useState([]);
  const [form,     setForm]    = useState(EMPTY);
  const [showAdd,  setShowAdd] = useState(false);
  const [saving,   setSaving]  = useState(false);
  const [removing, setRemoving]= useState(null);
  const [msg,      setMsg]     = useState("");

  const load = async () => {
    try {
      const r = await fetch(`${API}/appointments/`, { headers: { Authorization: `Bearer ${getToken()}` } });
      const data = await r.json();
      setAppts(Array.isArray(data) ? data.sort((a,b) => new Date(a.appointment_time) - new Date(b.appointment_time)) : []);
    } catch { setAppts([]); }
  };

  useEffect(() => { load(); }, []);

  const save = async () => {
    if (!form.doctor_name || !form.appointment_time) { setMsg("Doctor name and date/time are required."); return; }
    setSaving(true); setMsg("");
    try {
      const r = await fetch(`${API}/appointments/`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${getToken()}` },
        body: JSON.stringify(form),
      });
      const data = await r.json();
      if (r.ok) { setMsg("Appointment booked."); setForm(EMPTY); setShowAdd(false); load(); }
      else setMsg(data.detail || "Failed to book.");
    } catch { setMsg("Could not reach server."); }
    finally { setSaving(false); }
  };

  const remove = async (id) => {
    if (!window.confirm("Remove this appointment?")) return;
    setRemoving(id);
    try {
      await fetch(`${API}/appointments/${id}`, { method: "DELETE", headers: { Authorization: `Bearer ${getToken()}` } });
      setAppts((p) => p.filter((a) => a.id !== id));
    } catch { }
    finally { setRemoving(null); }
  };

  const upcoming = appts.filter((a) => new Date(a.appointment_time) >= new Date());
  const past     = appts.filter((a) => new Date(a.appointment_time) < new Date());

  return (
    <PageLayout>
      <div className="appt-page">

        <div className="appt-header">
          <div>
            <h1 className="appt-title">Appointments</h1>
            <p className="appt-sub">Schedule and manage your doctor visits</p>
          </div>
          <button className="appt-add-btn" onClick={() => { setShowAdd(true); setMsg(""); }}>
            + Book Appointment
          </button>
        </div>

        {msg && <div className={`appt-notice ${msg.includes("booked") ? "ok" : "err"}`}>{msg}</div>}

        {showAdd && (
          <div className="appt-form-card">
            <h2 className="appt-form-title">Book New Appointment</h2>
            <div className="appt-form-grid">
              <div className="appt-field">
                <label>Doctor Name <span>*</span></label>
                <input placeholder="Dr. Sharma" value={form.doctor_name} onChange={(e) => setForm({...form, doctor_name: e.target.value})} />
              </div>
              <div className="appt-field">
                <label>Clinic / Hospital</label>
                <input placeholder="Apollo Hospital" value={form.clinic_name} onChange={(e) => setForm({...form, clinic_name: e.target.value})} />
              </div>
              <div className="appt-field">
                <label>Date & Time <span>*</span></label>
                <input type="datetime-local" value={form.appointment_time} onChange={(e) => setForm({...form, appointment_time: e.target.value})} />
              </div>
              <div className="appt-field appt-field-full">
                <label>Notes</label>
                <textarea rows={2} placeholder="e.g. Follow-up for blood pressure, bring test reports…" value={form.notes} onChange={(e) => setForm({...form, notes: e.target.value})} />
              </div>
            </div>
            <div className="appt-form-actions">
              <button className="appt-btn-save" onClick={save} disabled={saving}>{saving ? "Saving…" : "Book Appointment"}</button>
              <button className="appt-btn-cancel" onClick={() => { setShowAdd(false); setForm(EMPTY); setMsg(""); }}>Cancel</button>
            </div>
          </div>
        )}

        {appts.length === 0 ? (
          <div className="appt-empty">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" width="48" height="48">
              <rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
            </svg>
            <p>No appointments yet</p>
            <span>Click "Book Appointment" to schedule your first visit</span>
          </div>
        ) : (
          <>
            {upcoming.length > 0 && (
              <section>
                <h2 className="appt-section-title">Upcoming ({upcoming.length})</h2>
                <div className="appt-grid">
                  {upcoming.map((a) => <ApptCard key={a.id} appt={a} onRemove={remove} removing={removing} highlight />)}
                </div>
              </section>
            )}
            {past.length > 0 && (
              <section>
                <h2 className="appt-section-title">Past Appointments</h2>
                <div className="appt-grid">
                  {past.map((a) => <ApptCard key={a.id} appt={a} onRemove={remove} removing={removing} />)}
                </div>
              </section>
            )}
          </>
        )}
      </div>
    </PageLayout>
  );
}

function ApptCard({ appt, onRemove, removing, highlight }) {
  const rel = relTime(appt.appointment_time);
  return (
    <div className={`appt-card ${highlight ? "appt-card-hl" : "appt-card-past"}`}>
      <div className="appt-card-top">
        <div className="appt-card-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" width="18" height="18">
            <rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
          </svg>
        </div>
        <div className="appt-card-info">
          <div className="appt-card-doctor">{appt.doctor_name}</div>
          {appt.clinic_name && <div className="appt-card-clinic">{appt.clinic_name}</div>}
        </div>
        <button className="appt-remove-btn" onClick={() => onRemove(appt.id)} disabled={removing === appt.id}>
          {removing === appt.id ? "…" : (
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="14" height="14">
              <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6M10 11v6M14 11v6M9 6V4h6v2"/>
            </svg>
          )}
        </button>
      </div>
      <div className="appt-card-time">{fmtDT(appt.appointment_time)}</div>
      <div className="appt-card-footer">
        {appt.notes && <span className="appt-card-notes">{appt.notes}</span>}
        <span className={`appt-badge ${rel === "Past" ? "past" : "upcoming"}`}>{rel}</span>
      </div>
    </div>
  );
}
