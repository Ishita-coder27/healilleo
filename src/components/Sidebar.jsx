import React from "react";
import "./Sidebar.css";

function Sidebar({ collapsed, toggleSidebar }) {
  return (
    <div className={`sidebar ${collapsed ? "collapsed" : ""}`}>

      {/* Header */}
      <div className="sidebar-header">
        <button onClick={toggleSidebar} className="toggle-btn">
          {collapsed ? "➡️" : "⬅️"}
        </button>
        {!collapsed && <h2>AI HEALTH</h2>}
      </div>

      {/* MAIN */}
      <p className="section-title">MAIN</p>
      <ul>
        <li>🏠 Dashboard</li>
      </ul>

      {/* HEALTH MANAGEMENT */}
      <p className="section-title">HEALTH MANAGEMENT</p>
      <ul>
        <li>🥗 Diet Plan</li>
        <li>🏋️ Exercise</li>
        <li>💊 Medicine Reminder</li>
      </ul>

      {/* HEALTH TRACKING */}
      <p className="section-title">HEALTH TRACKING</p>
      <ul>
        <li>😴 Sleep Tracker</li>
        <li>💧 Water Tracker</li>
        <li>📊 BMI Calculator</li>
      </ul>

      {/* MEDICAL */}
      <p className="section-title">MEDICAL</p>
      <ul>
        <li>📁 Medical Reports</li>
      </ul>

      {/* AI */}
      <p className="section-title">AI FEATURES</p>
      <ul>
        <li>🤖 AI Chatbot</li>
      </ul>

      {/* ACCOUNT */}
      <p className="section-title">ACCOUNT</p>
      <ul>
        <li>👤 Profile</li>
        <li>⚙️ Settings</li>
      </ul>

    </div>
  );
}

export default Sidebar;