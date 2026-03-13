import React, { useState, useRef } from "react";
import "./Navbar.css";

const API = "http://localhost:8000";

const NAV_ITEMS = [
  {
    label: "Update Reports",
    icon: "📁",
    dropdown: [
      { icon: "⬆️", label: "Upload New Report",  desc: "Add a new lab or medical report",   action: "upload-report"   },
      { icon: "🗑️", label: "Delete a Report",    desc: "Remove an existing report",         action: "delete-report"   },
      { icon: "📋", label: "View All Reports",   desc: "Browse your full report history",   action: "view-reports"    },
    ],
  },
  {
    label: "Appointments",
    icon: "🗓️",
    dropdown: [
      { icon: "➕", label: "New Appointment",       desc: "Schedule a new doctor visit",       action: "new-appointment"    },
      { icon: "❌", label: "Cancel Appointment",    desc: "Remove an upcoming appointment",    action: "cancel-appointment" },
      { icon: "📅", label: "View All Appointments", desc: "See your full appointment history", action: "view-appointments"  },
    ],
  },
  {
    label: "Medications",
    icon: "💊",
    dropdown: [
      { icon: "➕", label: "Add Medication",        desc: "Log a new medication & schedule",   action: "add-medication"    },
      { icon: "🗑️", label: "Remove Medication",    desc: "Delete a medication from your list", action: "remove-medication" },
      { icon: "📋", label: "View All Medications",  desc: "Browse your full medication list",  action: "view-medications"  },
    ],
  },
  { label: "BMI Check", icon: "📊", action: "open-bmi" },
  { label: "Diet Plan", icon: "🥗", href: "#" },
  { label: "Exercise",  icon: "🏋️", href: "#" },
];

const EMPTY_APPT = { doctor_name: "", clinic_name: "", appointment_time: "", notes: "" };
const EMPTY_MED  = { medication_name: "", dosage: "", frequency: "", start_date: "", end_date: "", notes: "", next_reminder_time: "" };

export default function Navbar({ openBMI }) {
  const [menuOpen,       setMenuOpen]       = useState(false);
  const [mobileExpanded, setMobileExpanded] = useState(null);

  // ── Shared modal state ──
  const [modal,     setModal]     = useState(null);
  const [modalMsg,  setModalMsg]  = useState("");
  const [saving,    setSaving]    = useState(false);

  // ── Reports state ──
  const [reports,   setReports]   = useState([]);
  const [uploading, setUploading] = useState(false);
  const [deleting,  setDeleting]  = useState(null);
  const [opening,   setOpening]   = useState(null);

  // ── Appointments state ──
  const [appointments,    setAppointments]    = useState([]);
  const [apptForm,        setApptForm]        = useState(EMPTY_APPT);
  const [cancellingAppt,  setCancellingAppt]  = useState(null);

  // ── Medications state ──
  const [medications,    setMedications]    = useState([]);
  const [medForm,        setMedForm]        = useState(EMPTY_MED);
  const [removingMed,    setRemovingMed]    = useState(null);

  const fileInputRef = useRef(null);
  const getToken = () => localStorage.getItem("heallio_token");

  // ── Fetchers ──
  const fetchReports = async () => {
    try {
      const res  = await fetch(`${API}/medical-reports/`, { headers: { Authorization: `Bearer ${getToken()}` } });
      const data = await res.json();
      setReports(Array.isArray(data) ? data : []);
    } catch { setReports([]); }
  };

  const fetchAppointments = async () => {
    try {
      const res  = await fetch(`${API}/appointments/`, { headers: { Authorization: `Bearer ${getToken()}` } });
      const data = await res.json();
      setAppointments(Array.isArray(data) ? data : []);
    } catch { setAppointments([]); }
  };

  const fetchMedications = async () => {
    try {
      const res  = await fetch(`${API}/medications/`, { headers: { Authorization: `Bearer ${getToken()}` } });
      const data = await res.json();
      setMedications(Array.isArray(data) ? data : []);
    } catch { setMedications([]); }
  };

  // ── Action dispatcher ──
  const handleAction = async (action) => {
    setModalMsg("");
    if (action === "upload-report") {
      fileInputRef.current?.click();
    } else if (action === "view-reports") {
      setModal("view-reports"); await fetchReports();
    } else if (action === "delete-report") {
      setModal("delete-report"); await fetchReports();
    } else if (action === "new-appointment") {
      setApptForm(EMPTY_APPT); setModal("new-appointment");
    } else if (action === "cancel-appointment") {
      setModal("cancel-appointment"); await fetchAppointments();
    } else if (action === "view-appointments") {
      setModal("view-appointments"); await fetchAppointments();
    } else if (action === "add-medication") {
      setMedForm(EMPTY_MED); setModal("add-medication");
    } else if (action === "remove-medication") {
      setModal("remove-medication"); await fetchMedications();
    } else if (action === "view-medications") {
      setModal("view-medications"); await fetchMedications();
    } else if (action === "open-bmi") {
      openBMI?.();
    }
  };

  // ── Report handlers ──
  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    if (file.type !== "application/pdf") {
      setModal("upload-status"); setModalMsg("❌ Only PDF files are accepted."); return;
    }
    setUploading(true); setModal("upload-status"); setModalMsg("Uploading…");
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res  = await fetch(`${API}/medical-reports/upload`, { method: "POST", headers: { Authorization: `Bearer ${getToken()}` }, body: formData });
      const data = await res.json();
      setModalMsg(res.ok ? `✅ "${data.file_name}" uploaded successfully!` : `❌ ${data.detail || "Upload failed."}`);
    } catch { setModalMsg("❌ Could not reach server."); }
    finally { setUploading(false); fileInputRef.current.value = ""; }
  };

  const handleOpen = async (id) => {
    setOpening(id);
    try {
      const res  = await fetch(`${API}/medical-reports/download/${id}`, { headers: { Authorization: `Bearer ${getToken()}` } });
      if (!res.ok) { alert("Could not open file."); return; }
      const blob = await res.blob();
      window.open(URL.createObjectURL(blob), "_blank");
    } catch { alert("Could not reach server."); }
    finally { setOpening(null); }
  };

  const handleDeleteReport = async (id, name) => {
    if (!window.confirm(`Delete "${name}"?`)) return;
    setDeleting(id);
    try {
      const res = await fetch(`${API}/medical-reports/delete/${id}`, { method: "DELETE", headers: { Authorization: `Bearer ${getToken()}` } });
      if (res.ok) setReports((prev) => prev.filter((r) => r.id !== id));
      else alert("Failed to delete report.");
    } catch { alert("Could not reach server."); }
    finally { setDeleting(null); }
  };

  // ── Appointment handlers ──
  const handleSaveAppointment = async () => {
    if (!apptForm.doctor_name || !apptForm.appointment_time) {
      setModalMsg("❌ Doctor name and date/time are required."); return;
    }
    setSaving(true); setModalMsg("");
    try {
      const res  = await fetch(`${API}/appointments/`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${getToken()}` },
        body: JSON.stringify(apptForm),
      });
      const data = await res.json();
      if (res.ok) { setModalMsg("✅ Appointment booked successfully!"); setApptForm(EMPTY_APPT); }
      else setModalMsg(`❌ ${data.detail || "Failed to book appointment."}`);
    } catch { setModalMsg("❌ Could not reach server."); }
    finally { setSaving(false); }
  };

  const handleCancelAppointment = async (id, name) => {
    if (!window.confirm(`Cancel appointment with ${name}?`)) return;
    setCancellingAppt(id);
    try {
      const res = await fetch(`${API}/appointments/${id}`, { method: "DELETE", headers: { Authorization: `Bearer ${getToken()}` } });
      if (res.ok) setAppointments((prev) => prev.filter((a) => a.id !== id));
      else alert("Failed to cancel appointment.");
    } catch { alert("Could not reach server."); }
    finally { setCancellingAppt(null); }
  };

  // ── Medication handlers ──
  const handleSaveMedication = async () => {
    if (!medForm.medication_name || !medForm.start_date) {
      setModalMsg("❌ Medication name and start date are required."); return;
    }
    setSaving(true); setModalMsg("");
    try {
      const res  = await fetch(`${API}/medications/`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${getToken()}` },
        body: JSON.stringify(medForm),
      });
      const data = await res.json();
      if (res.ok) { setModalMsg("✅ Medication added successfully!"); setMedForm(EMPTY_MED); }
      else setModalMsg(`❌ ${data.detail || "Failed to add medication."}`);
    } catch { setModalMsg("❌ Could not reach server."); }
    finally { setSaving(false); }
  };

  const handleRemoveMedication = async (id, name) => {
    if (!window.confirm(`Remove "${name}"?`)) return;
    setRemovingMed(id);
    try {
      const res = await fetch(`${API}/medications/${id}`, { method: "DELETE", headers: { Authorization: `Bearer ${getToken()}` } });
      if (res.ok) setMedications((prev) => prev.filter((m) => m.id !== id));
      else alert("Failed to remove medication.");
    } catch { alert("Could not reach server."); }
    finally { setRemovingMed(null); }
  };

  const closeModal = () => { setModal(null); setModalMsg(""); };

  // ── Helpers ──
  const fmtDateTime = (dt) => new Date(dt).toLocaleString("en-IN", { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
  const fmtDate     = (d)  => new Date(d).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });

  return (
    <>
      <nav className="hn-root">
        <div className="hn-inner">
          <a className="hn-logo" href="#">
            <span className="hn-logo-icon">🩺</span>
            <span className="hn-logo-text">Heallio</span>
          </a>

          <ul className="hn-links">
            {NAV_ITEMS.map((item) => (
              <li key={item.label} className={`hn-item ${item.dropdown ? "has-dropdown" : ""}`}>
                <a
  className="hn-link"
  href={item.href || "#"}
  onClick={(e) => {
    e.preventDefault();
    if (item.action) {
      handleAction(item.action);
    }
  }}
>
                  <span className="hn-link-icon">{item.icon}</span>
                  {item.label}
                  {item.dropdown && (
                    <svg className="hn-chevron" viewBox="0 0 10 6" fill="none">
                      <path d="M1 1l4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  )}
                </a>
                {item.dropdown && (
                  <div className="hn-dropdown">
                    {item.dropdown.map((d) => (
                      <button className="hn-dd-item" key={d.label} onClick={() => d.action && handleAction(d.action)}>
                        <span className="hn-dd-icon">{d.icon}</span>
                        <div>
                          <div className="hn-dd-label">{d.label}</div>
                          <div className="hn-dd-desc">{d.desc}</div>
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </li>
            ))}
          </ul>

          <div className="hn-right">
            <div className="hn-avatar">S</div>
          </div>

          <button className={`hn-hamburger ${menuOpen ? "open" : ""}`} onClick={() => setMenuOpen(!menuOpen)} aria-label="Toggle menu">
            <span /><span /><span />
          </button>
        </div>

        {menuOpen && (
          <div className="hn-mobile-menu">
            {NAV_ITEMS.map((item) => (
              <div key={item.label} className="hn-mobile-item">
                <button className="hn-mobile-link" onClick={() => {
                  if (item.action) {
                    handleAction(item.action);
                    setMenuOpen(false);
                  } else if (item.dropdown) {
                    setMobileExpanded((p) => (p === item.label ? null : item.label));
                  } else {
                    setMenuOpen(false);
                  }
                }}>
                  <span>{item.icon}</span>
                  {item.label}
                  {item.dropdown && (
                    <svg className={`hn-chevron ${mobileExpanded === item.label ? "flipped" : ""}`} viewBox="0 0 10 6" fill="none">
                      <path d="M1 1l4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  )}
                </button>
                {item.dropdown && mobileExpanded === item.label && (
                  <div className="hn-mobile-dropdown">
                    {item.dropdown.map((d) => (
                      <button className="hn-mobile-dd-item" key={d.label} onClick={() => { d.action && handleAction(d.action); setMenuOpen(false); }}>
                        <span>{d.icon}</span> {d.label}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </nav>

      <input ref={fileInputRef} type="file" accept=".pdf" style={{ display: "none" }} onChange={handleFileChange} />

      {/* ══════════════════ MODALS ══════════════════ */}
      {modal && (
        <div className="hn-modal-overlay" onClick={closeModal}>
          <div className="hn-modal" onClick={(e) => e.stopPropagation()}>

            {/* ── Upload status ── */}
            {modal === "upload-status" && (
              <>
                <div className="hn-modal-header">
                  <h2>Upload Report</h2>
                  <button className="hn-modal-close" onClick={closeModal}>✕</button>
                </div>
                <div className="hn-modal-body center">
                  <p className="hn-modal-msg">{uploading ? "⏳ Uploading your report…" : modalMsg}</p>
                  {!uploading && <button className="hn-modal-btn" onClick={closeModal}>Close</button>}
                </div>
              </>
            )}

            {/* ── View reports ── */}
            {modal === "view-reports" && (
              <>
                <div className="hn-modal-header">
                  <h2>📋 Your Medical Reports</h2>
                  <button className="hn-modal-close" onClick={closeModal}>✕</button>
                </div>
                <div className="hn-modal-body">
                  {reports.length === 0 ? <p className="hn-modal-empty">No reports uploaded yet.</p> : (
                    <ul className="hn-report-list">
                      {reports.map((r) => (
                        <li key={r.id} className="hn-report-item">
                          <span className="hn-report-icon">📄</span>
                          <div className="hn-report-info">
                            <div className="hn-report-name">{r.file_name}</div>
                            <div className="hn-report-date">{fmtDate(r.uploaded_at)}</div>
                          </div>
                          <span className={`hn-report-badge ${r.processed ? "processed" : "pending"}`}>
                            {r.processed ? "Processed" : "Pending"}
                          </span>
                          <button className="hn-view-btn" onClick={() => handleOpen(r.id)} disabled={opening === r.id}>
                            {opening === r.id ? "…" : "Open"}
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </>
            )}

            {/* ── Delete report ── */}
            {modal === "delete-report" && (
              <>
                <div className="hn-modal-header">
                  <h2>🗑️ Delete a Report</h2>
                  <button className="hn-modal-close" onClick={closeModal}>✕</button>
                </div>
                <div className="hn-modal-body">
                  {reports.length === 0 ? <p className="hn-modal-empty">No reports to delete.</p> : (
                    <ul className="hn-report-list">
                      {reports.map((r) => (
                        <li key={r.id} className="hn-report-item">
                          <span className="hn-report-icon">📄</span>
                          <div className="hn-report-info">
                            <div className="hn-report-name">{r.file_name}</div>
                            <div className="hn-report-date">{fmtDate(r.uploaded_at)}</div>
                          </div>
                          <button className="hn-delete-btn" onClick={() => handleDeleteReport(r.id, r.file_name)} disabled={deleting === r.id}>
                            {deleting === r.id ? "…" : "Delete"}
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </>
            )}

            {/* ── New appointment ── */}
            {modal === "new-appointment" && (
              <>
                <div className="hn-modal-header">
                  <h2>🗓️ New Appointment</h2>
                  <button className="hn-modal-close" onClick={closeModal}>✕</button>
                </div>
                <div className="hn-modal-body">
                  <div className="hn-form">
                    <div className="hn-form-field">
                      <label>Doctor Name <span className="hn-required">*</span></label>
                      <input placeholder="e.g. Dr. Sharma" value={apptForm.doctor_name} onChange={(e) => setApptForm({ ...apptForm, doctor_name: e.target.value })} />
                    </div>
                    <div className="hn-form-field">
                      <label>Clinic / Hospital</label>
                      <input placeholder="e.g. Apollo Hospital" value={apptForm.clinic_name} onChange={(e) => setApptForm({ ...apptForm, clinic_name: e.target.value })} />
                    </div>
                    <div className="hn-form-field">
                      <label>Date & Time <span className="hn-required">*</span></label>
                      <input type="datetime-local" value={apptForm.appointment_time} onChange={(e) => setApptForm({ ...apptForm, appointment_time: e.target.value })} />
                    </div>
                    <div className="hn-form-field">
                      <label>Notes / Reason</label>
                      <textarea placeholder="e.g. Annual checkup, blood pressure follow-up…" value={apptForm.notes} onChange={(e) => setApptForm({ ...apptForm, notes: e.target.value })} />
                    </div>
                    {modalMsg && <p className="hn-form-msg">{modalMsg}</p>}
                    <button className="hn-modal-btn full" onClick={handleSaveAppointment} disabled={saving}>
                      {saving ? "Saving…" : "Book Appointment"}
                    </button>
                  </div>
                </div>
              </>
            )}

            {/* ── Cancel appointment ── */}
            {modal === "cancel-appointment" && (
              <>
                <div className="hn-modal-header">
                  <h2>❌ Cancel Appointment</h2>
                  <button className="hn-modal-close" onClick={closeModal}>✕</button>
                </div>
                <div className="hn-modal-body">
                  {appointments.length === 0 ? <p className="hn-modal-empty">No appointments scheduled.</p> : (
                    <ul className="hn-report-list">
                      {appointments.map((a) => (
                        <li key={a.id} className="hn-report-item">
                          <span className="hn-report-icon">🗓️</span>
                          <div className="hn-report-info">
                            <div className="hn-report-name">{a.doctor_name}{a.clinic_name ? ` — ${a.clinic_name}` : ""}</div>
                            <div className="hn-report-date">{fmtDateTime(a.appointment_time)}</div>
                          </div>
                          <button className="hn-delete-btn" onClick={() => handleCancelAppointment(a.id, a.doctor_name)} disabled={cancellingAppt === a.id}>
                            {cancellingAppt === a.id ? "…" : "Cancel"}
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </>
            )}

            {/* ── View appointments ── */}
            {modal === "view-appointments" && (
              <>
                <div className="hn-modal-header">
                  <h2>📅 Your Appointments</h2>
                  <button className="hn-modal-close" onClick={closeModal}>✕</button>
                </div>
                <div className="hn-modal-body">
                  {appointments.length === 0 ? <p className="hn-modal-empty">No appointments scheduled.</p> : (
                    <ul className="hn-report-list">
                      {appointments.map((a) => (
                        <li key={a.id} className="hn-report-item">
                          <span className="hn-report-icon">🗓️</span>
                          <div className="hn-report-info">
                            <div className="hn-report-name">{a.doctor_name}{a.clinic_name ? ` — ${a.clinic_name}` : ""}</div>
                            <div className="hn-report-date">{fmtDateTime(a.appointment_time)}</div>
                            {a.notes && <div className="hn-report-notes">{a.notes}</div>}
                          </div>
                          <span className={`hn-report-badge ${a.reminder_sent ? "processed" : "pending"}`}>
                            {a.reminder_sent ? "Reminded" : "Upcoming"}
                          </span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </>
            )}

            {/* ── Add medication ── */}
            {modal === "add-medication" && (
              <>
                <div className="hn-modal-header">
                  <h2>💊 Add Medication</h2>
                  <button className="hn-modal-close" onClick={closeModal}>✕</button>
                </div>
                <div className="hn-modal-body">
                  <div className="hn-form">
                    <div className="hn-form-field">
                      <label>Medication Name <span className="hn-required">*</span></label>
                      <input placeholder="e.g. Metformin" value={medForm.medication_name} onChange={(e) => setMedForm({ ...medForm, medication_name: e.target.value })} />
                    </div>
                    <div className="hn-form-row">
                      <div className="hn-form-field">
                        <label>Dosage</label>
                        <input placeholder="e.g. 500mg" value={medForm.dosage} onChange={(e) => setMedForm({ ...medForm, dosage: e.target.value })} />
                      </div>
                      <div className="hn-form-field">
                        <label>Frequency</label>
                        <input placeholder="e.g. Twice daily" value={medForm.frequency} onChange={(e) => setMedForm({ ...medForm, frequency: e.target.value })} />
                      </div>
                    </div>
                    <div className="hn-form-row">
                      <div className="hn-form-field">
                        <label>Start Date <span className="hn-required">*</span></label>
                        <input type="date" value={medForm.start_date} onChange={(e) => setMedForm({ ...medForm, start_date: e.target.value })} />
                      </div>
                      <div className="hn-form-field">
                        <label>End Date</label>
                        <input type="date" value={medForm.end_date} onChange={(e) => setMedForm({ ...medForm, end_date: e.target.value })} />
                      </div>
                    </div>
                    <div className="hn-form-field">
                      <label>Next Reminder Time</label>
                      <input type="datetime-local" value={medForm.next_reminder_time} onChange={(e) => setMedForm({ ...medForm, next_reminder_time: e.target.value })} />
                    </div>
                    <div className="hn-form-field">
                      <label>Notes / Instructions</label>
                      <textarea placeholder="e.g. Take with meals, avoid grapefruit…" value={medForm.notes} onChange={(e) => setMedForm({ ...medForm, notes: e.target.value })} />
                    </div>
                    {modalMsg && <p className="hn-form-msg">{modalMsg}</p>}
                    <button className="hn-modal-btn full" onClick={handleSaveMedication} disabled={saving}>
                      {saving ? "Saving…" : "Add Medication"}
                    </button>
                  </div>
                </div>
              </>
            )}

            {/* ── Remove medication ── */}
            {modal === "remove-medication" && (
              <>
                <div className="hn-modal-header">
                  <h2>🗑️ Remove Medication</h2>
                  <button className="hn-modal-close" onClick={closeModal}>✕</button>
                </div>
                <div className="hn-modal-body">
                  {medications.length === 0 ? <p className="hn-modal-empty">No medications logged.</p> : (
                    <ul className="hn-report-list">
                      {medications.map((m) => (
                        <li key={m.id} className="hn-report-item">
                          <span className="hn-report-icon">💊</span>
                          <div className="hn-report-info">
                            <div className="hn-report-name">{m.medication_name}{m.dosage ? ` — ${m.dosage}` : ""}</div>
                            <div className="hn-report-date">{m.frequency || "No frequency set"}</div>
                          </div>
                          <button className="hn-delete-btn" onClick={() => handleRemoveMedication(m.id, m.medication_name)} disabled={removingMed === m.id}>
                            {removingMed === m.id ? "…" : "Remove"}
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </>
            )}

            {/* ── View medications ── */}
            {modal === "view-medications" && (
              <>
                <div className="hn-modal-header">
                  <h2>📋 Your Medications</h2>
                  <button className="hn-modal-close" onClick={closeModal}>✕</button>
                </div>
                <div className="hn-modal-body">
                  {medications.length === 0 ? <p className="hn-modal-empty">No medications logged.</p> : (
                    <ul className="hn-report-list">
                      {medications.map((m) => (
                        <li key={m.id} className="hn-report-item">
                          <span className="hn-report-icon">💊</span>
                          <div className="hn-report-info">
                            <div className="hn-report-name">{m.medication_name}{m.dosage ? ` — ${m.dosage}` : ""}</div>
                            <div className="hn-report-date">
                              {m.frequency && <span>{m.frequency} · </span>}
                              {fmtDate(m.start_date)}{m.end_date ? ` → ${fmtDate(m.end_date)}` : ""}
                            </div>
                            {m.notes && <div className="hn-report-notes">{m.notes}</div>}
                          </div>
                          <span className={`hn-report-badge ${m.reminder_sent ? "processed" : "pending"}`}>
                            {m.reminder_sent ? "Reminded" : "Active"}
                          </span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </>
            )}

          </div>
        </div>
      )}
    </>
  );
}