import React, { useState } from "react";
import PageLayout from "../components/PageLayout";
import ReactMarkdown from "react-markdown";
import "./DietPlan.css";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";
const getToken = () => localStorage.getItem("heallio_token");

const MEAL_PLAN = [
  { meal: "Breakfast", time: "7:00 – 8:00 AM", items: ["Oats with skimmed milk and banana", "1 boiled egg", "Green tea or water"] },
  { meal: "Mid-Morning", time: "10:30 AM", items: ["A handful of mixed nuts", "1 seasonal fruit"] },
  { meal: "Lunch", time: "1:00 – 2:00 PM", items: ["Brown rice or 2 chapatis", "Dal or legumes", "Vegetable curry", "Salad + curd"] },
  { meal: "Evening Snack", time: "4:30 PM", items: ["Sprouts chaat", "Buttermilk or coconut water"] },
  { meal: "Dinner", time: "7:00 – 8:00 PM", items: ["2 chapatis", "Sabzi (vegetables)", "Lentil soup", "Light salad"] },
];

const TIPS = [
  { title: "Stay Hydrated", desc: "Drink 8–10 glasses of water daily. Start your morning with a glass of warm water." },
  { title: "Reduce Sodium", desc: "Limit salt intake to under 5g per day. Avoid processed and packaged foods." },
  { title: "Eat More Fibre", desc: "Include whole grains, legumes, fruits, and vegetables to improve digestion." },
  { title: "Healthy Fats", desc: "Choose olive oil, avocado, and nuts over saturated and trans fats." },
  { title: "Mind Portions", desc: "Use smaller plates and eat slowly to naturally reduce calorie intake." },
  { title: "Limit Sugar", desc: "Reduce refined sugar — opt for natural sweetness from fruits instead." },
];

export default function DietPlan() {
  const [aiPlan,  setAiPlan]  = useState("");
  const [loading, setLoading] = useState(false);
  const [goal,    setGoal]    = useState("balanced");

  const generatePlan = async () => {
    setLoading(true); setAiPlan("");
    const prompt = `Generate a detailed, practical, one-week Indian diet plan for someone with a ${goal} health goal. Include breakfast, lunch, dinner and snacks for each day. Format with clear headings.`;
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

  return (
    <PageLayout>
      <div className="diet-page">
        <div className="diet-header">
          <div>
            <h1 className="diet-title">Diet Plan</h1>
            <p className="diet-sub">Personalised nutrition guidance for your health goals</p>
          </div>
        </div>

        {/* Goal selector + AI generate */}
        <div className="diet-ai-card">
          <h2 className="diet-section-title">Generate AI Diet Plan</h2>
          <p className="diet-ai-desc">Choose your goal and get a personalised weekly meal plan from AI</p>
          <div className="diet-goal-row">
            <select className="diet-select" value={goal} onChange={(e) => setGoal(e.target.value)}>
              <option value="balanced">Balanced Health</option>
              <option value="weight loss">Weight Loss</option>
              <option value="muscle gain">Muscle Gain</option>
              <option value="diabetes management">Diabetes Management</option>
              <option value="heart health">Heart Health</option>
              <option value="high blood pressure">High Blood Pressure</option>
            </select>
            <button className="diet-gen-btn" onClick={generatePlan} disabled={loading}>
              {loading ? <><span className="diet-spin" /> Generating…</> : "Generate Plan"}
            </button>
          </div>
          {aiPlan && (
            <div className="diet-ai-result">
              <ReactMarkdown>{aiPlan}</ReactMarkdown>
            </div>
          )}
          {loading && (
            <div className="diet-loading">
              <span className="diet-spin large" /> Crafting your personalised plan…
            </div>
          )}
        </div>

        {/* Default meal plan */}
        <div>
          <h2 className="diet-section-title">Recommended Daily Schedule</h2>
          <div className="diet-meals">
            {MEAL_PLAN.map((m) => (
              <div key={m.meal} className="diet-meal-card">
                <div className="diet-meal-header">
                  <span className="diet-meal-name">{m.meal}</span>
                  <span className="diet-meal-time">{m.time}</span>
                </div>
                <ul className="diet-meal-items">
                  {m.items.map((item) => <li key={item}>{item}</li>)}
                </ul>
              </div>
            ))}
          </div>
        </div>

        {/* Nutrition tips */}
        <div>
          <h2 className="diet-section-title">Nutrition Tips</h2>
          <div className="diet-tips">
            {TIPS.map((t) => (
              <div key={t.title} className="diet-tip-card">
                <div className="diet-tip-dot" />
                <div>
                  <div className="diet-tip-title">{t.title}</div>
                  <div className="diet-tip-desc">{t.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </PageLayout>
  );
}
