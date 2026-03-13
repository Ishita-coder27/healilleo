import React from "react";
import "./Sidebar.css";

const sections = [
  {
    title: "MAIN",
    items: [{ icon: "🏠", label: "Dashboard" }],
  },
  {
    title: "HEALTH MANAGEMENT",
    items: [
      { icon: "🥗", label: "Diet Plan" },
      { icon: "🏋️", label: "Exercise" },
      { icon: "💊", label: "Medicine Reminder" },
    ],
  },
  {
    title: "HEALTH TRACKING",
    items: [
      { icon: "😴", label: "Sleep Tracker" },
      { icon: "💧", label: "Water Tracker" },
      { icon: "📊", label: "BMI Calculator" },
    ],
  },
  {
    title: "MEDICAL",
    items: [{ icon: "📁", label: "Medical Reports" }],
  },
  {
    title: "AI FEATURES",
    items: [{ icon: "🤖", label: "AI Chatbot" }],
  },
  {
    title: "ACCOUNT",
    items: [
      { icon: "👤", label: "Profile" },
      { icon: "⚙️", label: "Settings" },
    ],
  },
];

function Sidebar({ collapsed, toggleSidebar, openBMI, openSleepTracker, openWaterTracker }) {
  return (
    <div className={`sidebar ${collapsed ? "collapsed" : ""}`}>

      {/* Header */}
      <div className="sidebar-header">
        {!collapsed && <h2 className="sidebar-brand">Heallio</h2>}
        <button onClick={toggleSidebar} className="toggle-btn">
          {collapsed ? "→" : "←"}
        </button>
      </div>

      {/* Nav sections */}
      <nav className="sidebar-nav">
        {sections.map((section) => (
          <div className="nav-section" key={section.title}>
            {!collapsed && (
              <p className="section-title">{section.title}</p>
            )}
            <ul>
              {section.items.map((item) => {
                const isBMI = item.label === "BMI Calculator";
                const isSleep = item.label === "Sleep Tracker";
                const isWater = item.label === "Water Tracker";
                return (
                  <li 
                    key={item.label} 
                    className="nav-item" 
                    title={collapsed ? item.label : ""} 
                    onClick={() => {
                      if (isBMI) openBMI?.();
                      if (isSleep) openSleepTracker?.();
                      if (isWater) openWaterTracker?.();
                    }}
                  >
                    <span className="nav-icon">{item.icon}</span>
                    {!collapsed && <span className="nav-label">{item.label}</span>}
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

    </div>
  );
}

export default Sidebar;