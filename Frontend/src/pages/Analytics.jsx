import React, { useState, useEffect } from "react";
import Sidebar from "../components/Sidebar";
import Navbar from "../components/Navbar";
import BMICalculator from "../components/BMICalculator";
import {
  LineChart, Line, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from "recharts";
import "./Analytics.css";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

/* ── Fallback demo data when backend is unreachable ── */
const DEMO_VITALS = [
  { date: "Jun 10", heart_rate: 74, systolic: 118, diastolic: 76, glucose: 92 },
  { date: "Jun 11", heart_rate: 78, systolic: 122, diastolic: 80, glucose: 95 },
  { date: "Jun 12", heart_rate: 72, systolic: 119, diastolic: 77, glucose: 88 },
  { date: "Jun 13", heart_rate: 80, systolic: 125, diastolic: 82, glucose: 100 },
  { date: "Jun 14", heart_rate: 76, systolic: 120, diastolic: 78, glucose: 91 },
  { date: "Jun 15", heart_rate: 75, systolic: 117, diastolic: 75, glucose: 89 },
  { date: "Jun 16", heart_rate: 77, systolic: 121, diastolic: 79, glucose: 94 },
];

const DEMO_SLEEP = [
  { date: "Mon", hours: 6.5 },
  { date: "Tue", hours: 7.0 },
  { date: "Wed", hours: 5.5 },
  { date: "Thu", hours: 8.0 },
  { date: "Fri", hours: 7.5 },
  { date: "Sat", hours: 9.0 },
  { date: "Sun", hours: 7.0 },
];

const DEMO_WATER = [
  { date: "Mon", glasses: 6 },
  { date: "Tue", glasses: 8 },
  { date: "Wed", glasses: 5 },
  { date: "Thu", glasses: 8 },
  { date: "Fri", glasses: 7 },
  { date: "Sat", glasses: 6 },
  { date: "Sun", glasses: 9 },
];

const SCORE_FACTORS = [
  { label: "Heart Rate", key: "heart_rate", ideal: [60, 100], unit: "bpm" },
  { label: "Blood Pressure", key: "systolic",  ideal: [90, 120],  unit: "mmHg" },
  { label: "Glucose",       key: "glucose",    ideal: [70, 99],   unit: "mg/dL" },
];

function calcHealthScore(latest) {
  if (!latest) return 72;
  let score = 100;
  SCORE_FACTORS.forEach(({ key, ideal }) => {
    const val = latest[key];
    if (!val) return;
    if (val < ideal[0]) score -= Math.min(15, (ideal[0] - val) * 1.5);
    if (val > ideal[1]) score -= Math.min(15, (val - ideal[1]) * 1.5);
  });
  return Math.max(0, Math.round(score));
}

function ScoreRing({ score }) {
  const radius = 54;
  const circ = 2 * Math.PI * radius;
  const fill = (score / 100) * circ;
  const color = score >= 80 ? "#22C55E" : score >= 60 ? "#F59E0B" : "#EF4444";

  return (
    <div className="an-score-ring-wrap">
      <svg width="140" height="140" viewBox="0 0 140 140">
        <circle cx="70" cy="70" r={radius} fill="none" stroke="var(--border)" strokeWidth="12" />
        <circle
          cx="70" cy="70" r={radius}
          fill="none"
          stroke={color}
          strokeWidth="12"
          strokeLinecap="round"
          strokeDasharray={`${fill} ${circ}`}
          transform="rotate(-90 70 70)"
          style={{ transition: "stroke-dasharray 1s ease" }}
        />
      </svg>
      <div className="an-score-center">
        <span className="an-score-num" style={{ color }}>{score}</span>
        <span className="an-score-label">/ 100</span>
      </div>
    </div>
  );
}

const CUSTOM_TOOLTIP = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="an-tooltip">
      <p className="an-tooltip-label">{label}</p>
      {payload.map((p) => (
        <p key={p.dataKey} style={{ color: p.color }}>
          {p.name}: <strong>{p.value}</strong>
        </p>
      ))}
    </div>
  );
};

export default function Analytics() {
  const [vitals,  setVitals]  = useState(DEMO_VITALS);
  const [sleep,   setSleep]   = useState(DEMO_SLEEP);
  const [water,   setWater]   = useState(DEMO_WATER);
  const [loading, setLoading] = useState(true);
  const [demo,    setDemo]    = useState(false);
  const [bmiOpen, setBmiOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("heallio_token");
    if (!token) { setDemo(true); setLoading(false); return; }

    fetch(`${API}/vitals/`, { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => r.json())
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          const formatted = data.slice(-14).map((v) => ({
            date: new Date(v.recorded_at || v.created_at).toLocaleDateString("en-IN", { day: "numeric", month: "short" }),
            heart_rate: v.heart_rate,
            systolic:   v.blood_pressure_systolic,
            diastolic:  v.blood_pressure_diastolic,
            glucose:    v.blood_glucose,
          }));
          setVitals(formatted);
        } else {
          setDemo(true);
        }
      })
      .catch(() => setDemo(true))
      .finally(() => setLoading(false));
  }, []);

  const latest = vitals[vitals.length - 1] || {};
  const score  = calcHealthScore(latest);

  const stats = [
    { label: "Avg Heart Rate", value: Math.round(vitals.reduce((s, v) => s + (v.heart_rate || 0), 0) / vitals.length), unit: "bpm", color: "#EF4444" },
    { label: "Avg Systolic BP", value: Math.round(vitals.reduce((s, v) => s + (v.systolic || 0), 0) / vitals.length), unit: "mmHg", color: "#8B5CF6" },
    { label: "Avg Glucose", value: Math.round(vitals.reduce((s, v) => s + (v.glucose || 0), 0) / vitals.length), unit: "mg/dL", color: "#F59E0B" },
    { label: "Avg Sleep", value: (sleep.reduce((s, v) => s + v.hours, 0) / sleep.length).toFixed(1), unit: "hrs", color: "#06B6D4" },
  ];

  return (
    <div className="heallio-layout">
      <Sidebar
        collapsed={collapsed}
        toggleSidebar={() => setCollapsed(!collapsed)}
        openBMI={() => setBmiOpen(true)}
      />
      <div className={`heallio-main ${collapsed ? "sidebar-collapsed" : ""}`}>
        <Navbar openBMI={() => setBmiOpen(true)} />

        <div className="heallio-content an-content">
          <div className="an-page-header">
            <div>
              <h1 className="an-title">Health Analytics</h1>
              <p className="an-sub">Your health trends at a glance</p>
            </div>
            {demo && (
              <span className="an-demo-badge">📊 Demo Data — connect backend for live charts</span>
            )}
          </div>

          {loading ? (
            <div className="an-loading">Loading your data…</div>
          ) : (
            <>
              {/* ── Score + Stats ── */}
              <div className="an-top-row">
                <div className="an-score-card">
                  <ScoreRing score={score} />
                  <div className="an-score-info">
                    <h3>Health Score</h3>
                    <p>{score >= 80 ? "Excellent — keep it up!" : score >= 60 ? "Good — room to improve" : "Needs attention"}</p>
                  </div>
                </div>
                <div className="an-stats-grid">
                  {stats.map((s) => (
                    <div key={s.label} className="an-stat-card">
                      <div className="an-stat-value" style={{ color: s.color }}>{s.value}<span className="an-stat-unit">{s.unit}</span></div>
                      <div className="an-stat-label">{s.label}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* ── Vitals Trend Chart ── */}
              <div className="an-chart-card">
                <h2 className="an-chart-title">Vitals Over Time</h2>
                <ResponsiveContainer width="100%" height={260}>
                  <LineChart data={vitals} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                    <XAxis dataKey="date" tick={{ fontSize: 12, fill: "var(--text-2)" }} />
                    <YAxis tick={{ fontSize: 12, fill: "var(--text-2)" }} />
                    <Tooltip content={<CUSTOM_TOOLTIP />} />
                    <Legend />
                    <Line type="monotone" dataKey="heart_rate" name="Heart Rate" stroke="#EF4444" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="systolic"   name="BP Systolic" stroke="#8B5CF6" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="glucose"    name="Glucose"     stroke="#F59E0B" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {/* ── Sleep + Water ── */}
              <div className="an-charts-row">
                <div className="an-chart-card">
                  <h2 className="an-chart-title">Sleep This Week</h2>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={sleep} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                      <XAxis dataKey="date" tick={{ fontSize: 12, fill: "var(--text-2)" }} />
                      <YAxis domain={[0, 10]} tick={{ fontSize: 12, fill: "var(--text-2)" }} />
                      <Tooltip content={<CUSTOM_TOOLTIP />} />
                      <Bar dataKey="hours" name="Hours" fill="#06B6D4" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                  <div className="an-goal-line">🎯 Goal: 8 hrs/night</div>
                </div>

                <div className="an-chart-card">
                  <h2 className="an-chart-title">Water Intake This Week</h2>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={water} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                      <XAxis dataKey="date" tick={{ fontSize: 12, fill: "var(--text-2)" }} />
                      <YAxis domain={[0, 10]} tick={{ fontSize: 12, fill: "var(--text-2)" }} />
                      <Tooltip content={<CUSTOM_TOOLTIP />} />
                      <Bar dataKey="glasses" name="Glasses" fill="#22C55E" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                  <div className="an-goal-line">🎯 Goal: 8 glasses/day</div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
      <BMICalculator open={bmiOpen} onClose={() => setBmiOpen(false)} />
    </div>
  );
}
