import React, { useState, useEffect } from "react";
import PageLayout from "../components/PageLayout";
import "./Profile.css";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";
const getToken = () => localStorage.getItem("heallio_token");

const EMPTY_PROFILE = { full_name: "", email: "", phone: "", date_of_birth: "", gender: "", height_cm: "", weight_kg: "", blood_group: "", allergies: "", existing_conditions: "", emergency_contact_name: "", emergency_contact_phone: "" };

export default function Profile() {
  const [profile, setProfile] = useState(EMPTY_PROFILE);
  const [editing, setEditing] = useState(false);
  const [saving,  setSaving]  = useState(false);
  const [msg,     setMsg]     = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = JSON.parse(localStorage.getItem("heallio_user") || "{}");
    if (stored.email) {
      setProfile((p) => ({
        ...p,
        full_name: stored.full_name || stored.name || "",
        email:     stored.email || "",
      }));
    }
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    setLoading(true);
    try {
      const r = await fetch(`${API}/profile/`, { headers: { Authorization: `Bearer ${getToken()}` } });
      if (r.ok) {
        const data = await r.json();
        setProfile((p) => ({ ...p, ...data }));
      }
    } catch { /* use defaults */ }
    finally { setLoading(false); }
  };

  const save = async () => {
    setSaving(true); setMsg("");
    try {
      const r = await fetch(`${API}/profile/`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${getToken()}` },
        body: JSON.stringify(profile),
      });
      if (r.ok) { setMsg("Profile updated."); setEditing(false); }
      else { const d = await r.json(); setMsg(d.detail || "Failed to update."); }
    } catch { setMsg("Could not reach server."); }
    finally { setSaving(false); }
  };

  const change = (key) => (e) => setProfile((p) => ({ ...p, [key]: e.target.value }));

  const initials = (profile.full_name || "U").split(" ").map((w) => w[0]).slice(0, 2).join("").toUpperCase();

  return (
    <PageLayout>
      <div className="prof-page">
        <div className="prof-header">
          <div>
            <h1 className="prof-title">Profile</h1>
            <p className="prof-sub">Manage your health profile and personal details</p>
          </div>
          {!editing && (
            <button className="prof-edit-btn" onClick={() => { setEditing(true); setMsg(""); }}>
              Edit Profile
            </button>
          )}
        </div>

        {msg && <div className={`prof-notice ${msg.includes("updated") ? "ok" : "err"}`}>{msg}</div>}

        {loading ? (
          <div className="prof-loading"><span className="prof-spin" /> Loading profile…</div>
        ) : (
          <div className="prof-body">
            {/* Avatar card */}
            <div className="prof-avatar-card">
              <div className="prof-avatar">{initials}</div>
              <div className="prof-avatar-name">{profile.full_name || "Your Name"}</div>
              <div className="prof-avatar-email">{profile.email}</div>
              {profile.blood_group && (
                <div className="prof-blood">Blood Group: <strong>{profile.blood_group}</strong></div>
              )}
              <div className="prof-stats">
                {profile.height_cm && <div className="prof-stat"><span className="prof-stat-val">{profile.height_cm}</span><span className="prof-stat-lbl">Height (cm)</span></div>}
                {profile.weight_kg && <div className="prof-stat"><span className="prof-stat-val">{profile.weight_kg}</span><span className="prof-stat-lbl">Weight (kg)</span></div>}
                {profile.height_cm && profile.weight_kg && (
                  <div className="prof-stat">
                    <span className="prof-stat-val">{(profile.weight_kg / ((profile.height_cm / 100) ** 2)).toFixed(1)}</span>
                    <span className="prof-stat-lbl">BMI</span>
                  </div>
                )}
              </div>
            </div>

            {/* Details */}
            <div className="prof-details">

              <section className="prof-section">
                <h2 className="prof-section-title">Personal Information</h2>
                <div className="prof-grid">
                  <Field label="Full Name"     value={profile.full_name}    editing={editing} onChange={change("full_name")} />
                  <Field label="Email"          value={profile.email}        editing={false}   onChange={() => {}} />
                  <Field label="Phone"          value={profile.phone}        editing={editing} onChange={change("phone")} placeholder="+91 XXXXX XXXXX" />
                  <Field label="Date of Birth"  value={profile.date_of_birth} editing={editing} onChange={change("date_of_birth")} type="date" />
                  <Field label="Gender"         value={profile.gender}       editing={editing} onChange={change("gender")} select={["", "Male", "Female", "Non-binary", "Prefer not to say"]} />
                </div>
              </section>

              <section className="prof-section">
                <h2 className="prof-section-title">Physical Health</h2>
                <div className="prof-grid">
                  <Field label="Height (cm)"    value={profile.height_cm}   editing={editing} onChange={change("height_cm")}   type="number" placeholder="e.g. 170" />
                  <Field label="Weight (kg)"    value={profile.weight_kg}   editing={editing} onChange={change("weight_kg")}   type="number" placeholder="e.g. 65" />
                  <Field label="Blood Group"    value={profile.blood_group}  editing={editing} onChange={change("blood_group")} select={["", "A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]} />
                </div>
              </section>

              <section className="prof-section">
                <h2 className="prof-section-title">Medical Information</h2>
                <div className="prof-grid">
                  <Field label="Known Allergies" value={profile.allergies} editing={editing} onChange={change("allergies")} placeholder="e.g. Penicillin, Peanuts" fullWidth />
                  <Field label="Existing Conditions" value={profile.existing_conditions} editing={editing} onChange={change("existing_conditions")} placeholder="e.g. Hypertension, Type 2 Diabetes" fullWidth />
                </div>
              </section>

              <section className="prof-section">
                <h2 className="prof-section-title">Emergency Contact</h2>
                <div className="prof-grid">
                  <Field label="Contact Name"  value={profile.emergency_contact_name}  editing={editing} onChange={change("emergency_contact_name")}  placeholder="Full name" />
                  <Field label="Contact Phone" value={profile.emergency_contact_phone} editing={editing} onChange={change("emergency_contact_phone")} placeholder="+91 XXXXX XXXXX" />
                </div>
              </section>

              {editing && (
                <div className="prof-form-actions">
                  <button className="prof-btn-save" onClick={save} disabled={saving}>{saving ? "Saving…" : "Save Changes"}</button>
                  <button className="prof-btn-cancel" onClick={() => { setEditing(false); setMsg(""); fetchProfile(); }}>Cancel</button>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </PageLayout>
  );
}

function Field({ label, value, editing, onChange, type = "text", placeholder, select, fullWidth }) {
  return (
    <div className={`prof-field ${fullWidth ? "prof-field-full" : ""}`}>
      <label className="prof-field-label">{label}</label>
      {editing ? (
        select ? (
          <select className="prof-input" value={value || ""} onChange={onChange}>
            {select.map((o) => <option key={o} value={o}>{o || "— Select —"}</option>)}
          </select>
        ) : (
          <input className="prof-input" type={type} value={value || ""} onChange={onChange} placeholder={placeholder} />
        )
      ) : (
        <div className="prof-value">{value || <span className="prof-empty-val">Not provided</span>}</div>
      )}
    </div>
  );
}
