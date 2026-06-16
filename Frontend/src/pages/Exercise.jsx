import React, { useState } from "react";
import PageLayout from "../components/PageLayout";
import ReactMarkdown from "react-markdown";
import "./Exercise.css";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";
const getToken = () => localStorage.getItem("heallio_token");

const PLANS = {
  beginner: [
    { day: "Monday",    label: "Full Body",       exercises: ["10 squats × 3", "10 push-ups × 3 (modified ok)", "15 glute bridges × 3", "20 min walk"] },
    { day: "Tuesday",   label: "Active Rest",      exercises: ["30 min gentle walk", "Light stretching (10 min)"] },
    { day: "Wednesday", label: "Upper Body",       exercises: ["10 wall push-ups × 3", "10 dumbbell rows × 3 (light)", "10 shoulder press × 3 (light)", "Plank 20s × 3"] },
    { day: "Thursday",  label: "Active Rest",      exercises: ["Yoga or stretching (20 min)"] },
    { day: "Friday",    label: "Lower Body",       exercises: ["15 squats × 3", "15 lunges × 3", "20 calf raises × 3", "20 min brisk walk"] },
    { day: "Saturday",  label: "Cardio",           exercises: ["20–30 min brisk walk or light jog", "Cool-down stretches (10 min)"] },
    { day: "Sunday",    label: "Rest",             exercises: ["Complete rest or light stretching"] },
  ],
  intermediate: [
    { day: "Monday",    label: "Push",             exercises: ["Bench press 4×8", "Overhead press 3×10", "Incline dumbbell press 3×12", "Tricep dips 3×12"] },
    { day: "Tuesday",   label: "Pull + Core",      exercises: ["Pull-ups 4×6", "Barbell rows 3×10", "Lat pulldown 3×12", "Plank 60s × 3"] },
    { day: "Wednesday", label: "Legs",             exercises: ["Squats 4×8", "Romanian deadlift 3×10", "Leg press 3×12", "Calf raises 4×15"] },
    { day: "Thursday",  label: "Active Rest",      exercises: ["20–30 min cardio", "Foam rolling & stretching"] },
    { day: "Friday",    label: "Full Body Strength", exercises: ["Deadlift 4×5", "Push-ups 4×15", "Dumbbell lunge 3×12", "Face pull 3×15"] },
    { day: "Saturday",  label: "Cardio / HIIT",    exercises: ["20 min HIIT (30s on / 30s off)", "Burpees, mountain climbers, jump squats"] },
    { day: "Sunday",    label: "Rest",             exercises: ["Complete rest"] },
  ],
};

const TIPS = [
  { title: "Warm Up First", desc: "Spend 5–10 minutes warming up with light cardio and dynamic stretches before each session." },
  { title: "Progressive Overload", desc: "Gradually increase weight, reps, or duration each week to continue making gains." },
  { title: "Rest and Recover", desc: "Muscles grow during rest, not during workouts. Sleep 7–9 hours and take rest days." },
  { title: "Stay Consistent", desc: "Three focused workouts per week consistently beats seven half-hearted ones." },
  { title: "Track Your Sessions", desc: "Log exercises, weights, and reps. Seeing progress is a powerful motivator." },
  { title: "Consult a Specialist", desc: "If you have any medical conditions, consult your doctor before starting a new routine." },
];

export default function Exercise() {
  const [level,   setLevel]   = useState("beginner");
  const [aiPlan,  setAiPlan]  = useState("");
  const [loading, setLoading] = useState(false);
  const [goal,    setGoal]    = useState("general fitness");

  const generatePlan = async () => {
    setLoading(true); setAiPlan("");
    const prompt = `Create a detailed, safe, week-long ${level} level exercise plan for someone with a goal of ${goal}. Include sets, reps, rest periods, and notes on form. Format with clear day-by-day headings.`;
    try {
      const storedUser = JSON.parse(localStorage.getItem("heallio_user") || "{}");
      const r = await fetch(`${API}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${getToken()}` },
        body: JSON.stringify({ user_id: storedUser.id ?? 1, message: prompt }),
      });
      const data = await r.json();
      setAiPlan(data.reply || "Could not generate plan. Please try again.");
    } catch { setAiPlan("Could not reach the AI service. Make sure the backend is running."); }
    finally { setLoading(false); }
  };

  const plan = PLANS[level] || PLANS.beginner;

  return (
    <PageLayout>
      <div className="ex-page">
        <div className="ex-header">
          <div>
            <h1 className="ex-title">Exercise Plan</h1>
            <p className="ex-sub">Science-backed fitness routines tailored to your level</p>
          </div>
          <div className="ex-level-tabs">
            {["beginner", "intermediate"].map((l) => (
              <button key={l} className={`ex-tab ${level === l ? "active" : ""}`} onClick={() => setLevel(l)}>
                {l.charAt(0).toUpperCase() + l.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* AI generator */}
        <div className="ex-ai-card">
          <h2 className="ex-section-title">Generate AI Exercise Plan</h2>
          <p className="ex-ai-desc">Get a personalised plan based on your specific fitness goal</p>
          <div className="ex-ai-row">
            <select className="ex-select" value={goal} onChange={(e) => setGoal(e.target.value)}>
              <option value="general fitness">General Fitness</option>
              <option value="weight loss">Weight Loss</option>
              <option value="muscle gain">Muscle Gain</option>
              <option value="improved cardiovascular health">Cardio Health</option>
              <option value="flexibility and mobility">Flexibility & Mobility</option>
              <option value="diabetes management">Diabetes Management</option>
              <option value="high blood pressure management">Blood Pressure Management</option>
            </select>
            <select className="ex-select" value={level} onChange={(e) => setLevel(e.target.value)}>
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
            </select>
            <button className="ex-gen-btn" onClick={generatePlan} disabled={loading}>
              {loading ? <><span className="ex-spin" /> Generating…</> : "Generate Plan"}
            </button>
          </div>
          {loading && <div className="ex-loading"><span className="ex-spin large" /> Crafting your personalised plan…</div>}
          {aiPlan && <div className="ex-ai-result"><ReactMarkdown>{aiPlan}</ReactMarkdown></div>}
        </div>

        {/* Weekly plan */}
        <div>
          <h2 className="ex-section-title">Weekly {level.charAt(0).toUpperCase() + level.slice(1)} Plan</h2>
          <div className="ex-week">
            {plan.map((d) => (
              <div key={d.day} className={`ex-day-card ${d.label === "Rest" || d.label === "Active Rest" ? "ex-day-rest" : ""}`}>
                <div className="ex-day-head">
                  <span className="ex-day-name">{d.day}</span>
                  <span className="ex-day-label">{d.label}</span>
                </div>
                <ul className="ex-day-items">
                  {d.exercises.map((e) => <li key={e}>{e}</li>)}
                </ul>
              </div>
            ))}
          </div>
        </div>

        {/* Tips */}
        <div>
          <h2 className="ex-section-title">Training Tips</h2>
          <div className="ex-tips">
            {TIPS.map((t) => (
              <div key={t.title} className="ex-tip-card">
                <div className="ex-tip-dot" />
                <div>
                  <div className="ex-tip-title">{t.title}</div>
                  <div className="ex-tip-desc">{t.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </PageLayout>
  );
}
