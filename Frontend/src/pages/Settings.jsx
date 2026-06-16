import React, { useState } from "react";
import PageLayout from "../components/PageLayout";
import { useTheme } from "../context/ThemeContext";
import "./Settings.css";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";
const getToken = () => localStorage.getItem("heallio_token");

export default function Settings() {
  const { dark, toggle } = useTheme();
  const [msg, setMsg] = useState("");
  const [saving, setSaving] = useState(false);
  const [pwForm, setPwForm] = useState({ current_password: "", new_password: "", confirm_password: "" });
  const [notifs, setNotifs] = useState({ medication_reminders: true, health_tips: true, report_alerts: true });
  const [units,  setUnits]  = useState({ height: "cm", weight: "kg" });
  const [deleteConfirm, setDeleteConfirm] = useState("");

  const savePassword = async () => {
    if (!pwForm.current_password || !pwForm.new_password) { setMsg("Please fill in all password fields."); return; }
    if (pwForm.new_password !== pwForm.confirm_password) { setMsg("New passwords do not match."); return; }
    if (pwForm.new_password.length < 8) { setMsg("Password must be at least 8 characters."); return; }
    setSaving(true); setMsg("");
    try {
      const r = await fetch(`${API}/auth/change-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${getToken()}` },
        body: JSON.stringify({ current_password: pwForm.current_password, new_password: pwForm.new_password }),
      });
      const data = await r.json();
      if (r.ok) { setMsg("Password changed successfully."); setPwForm({ current_password: "", new_password: "", confirm_password: "" }); }
      else setMsg(data.detail || "Failed to change password.");
    } catch { setMsg("Could not reach server."); }
    finally { setSaving(false); }
  };

  return (
    <PageLayout>
      <div className="sett-page">
        <div className="sett-header">
          <h1 className="sett-title">Settings</h1>
          <p className="sett-sub">Manage your preferences and account settings</p>
        </div>

        {msg && (
          <div className={`sett-notice ${msg.toLowerCase().includes("success") || msg.toLowerCase().includes("changed") ? "ok" : "err"}`}>
            {msg}
          </div>
        )}

        {/* Appearance */}
        <section className="sett-card">
          <h2 className="sett-section-title">Appearance</h2>
          <div className="sett-row">
            <div className="sett-row-info">
              <div className="sett-row-label">Dark Mode</div>
              <div className="sett-row-desc">Switch between light and dark interface</div>
            </div>
            <button className={`sett-toggle ${dark ? "on" : ""}`} onClick={toggle} aria-label="Toggle dark mode">
              <span className="sett-toggle-thumb" />
            </button>
          </div>
        </section>

        {/* Units */}
        <section className="sett-card">
          <h2 className="sett-section-title">Measurement Units</h2>
          <div className="sett-row">
            <div className="sett-row-info">
              <div className="sett-row-label">Height</div>
              <div className="sett-row-desc">Unit used for height measurements</div>
            </div>
            <div className="sett-segmented">
              {["cm", "ft"].map((u) => (
                <button key={u} className={`sett-seg-btn ${units.height === u ? "active" : ""}`} onClick={() => setUnits((p) => ({ ...p, height: u }))}>
                  {u}
                </button>
              ))}
            </div>
          </div>
          <div className="sett-row">
            <div className="sett-row-info">
              <div className="sett-row-label">Weight</div>
              <div className="sett-row-desc">Unit used for weight measurements</div>
            </div>
            <div className="sett-segmented">
              {["kg", "lbs"].map((u) => (
                <button key={u} className={`sett-seg-btn ${units.weight === u ? "active" : ""}`} onClick={() => setUnits((p) => ({ ...p, weight: u }))}>
                  {u}
                </button>
              ))}
            </div>
          </div>
        </section>

        {/* Notifications */}
        <section className="sett-card">
          <h2 className="sett-section-title">Notifications</h2>
          {[
            { key: "medication_reminders", label: "Medication Reminders",   desc: "Get reminded when it's time for a dose" },
            { key: "health_tips",          label: "Daily Health Tips",       desc: "Receive personalised daily wellness tips" },
            { key: "report_alerts",        label: "Report Analysis Alerts",  desc: "Notify when AI finishes analysing a report" },
          ].map(({ key, label, desc }) => (
            <div key={key} className="sett-row">
              <div className="sett-row-info">
                <div className="sett-row-label">{label}</div>
                <div className="sett-row-desc">{desc}</div>
              </div>
              <button
                className={`sett-toggle ${notifs[key] ? "on" : ""}`}
                onClick={() => setNotifs((p) => ({ ...p, [key]: !p[key] }))}
                aria-label={label}
              >
                <span className="sett-toggle-thumb" />
              </button>
            </div>
          ))}
        </section>

        {/* Password */}
        <section className="sett-card">
          <h2 className="sett-section-title">Change Password</h2>
          <div className="sett-pw-form">
            <div className="sett-field">
              <label>Current Password</label>
              <input type="password" value={pwForm.current_password} onChange={(e) => setPwForm((p) => ({ ...p, current_password: e.target.value }))} placeholder="Enter current password" />
            </div>
            <div className="sett-field">
              <label>New Password</label>
              <input type="password" value={pwForm.new_password} onChange={(e) => setPwForm((p) => ({ ...p, new_password: e.target.value }))} placeholder="At least 8 characters" />
            </div>
            <div className="sett-field">
              <label>Confirm New Password</label>
              <input type="password" value={pwForm.confirm_password} onChange={(e) => setPwForm((p) => ({ ...p, confirm_password: e.target.value }))} placeholder="Repeat new password" />
            </div>
            <button className="sett-save-btn" onClick={savePassword} disabled={saving}>
              {saving ? "Saving…" : "Update Password"}
            </button>
          </div>
        </section>

        {/* Danger zone */}
        <section className="sett-card sett-danger-card">
          <h2 className="sett-section-title">Danger Zone</h2>
          <div className="sett-row">
            <div className="sett-row-info">
              <div className="sett-row-label sett-danger-label">Delete Account</div>
              <div className="sett-row-desc">Permanently delete your account and all health data. This cannot be undone.</div>
            </div>
            <button
              className="sett-delete-btn"
              onClick={() => {
                const c = window.prompt('Type "DELETE" to confirm account deletion:');
                if (c === "DELETE") alert("Account deletion request submitted. Our team will process this within 48 hours.");
              }}
            >
              Delete Account
            </button>
          </div>
        </section>
      </div>
    </PageLayout>
  );
}
