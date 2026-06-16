import React from "react";
import { useNavigate, useLocation } from "react-router-dom";
import "./Sidebar.css";

/* ── SVG icon set — no emojis ─────────────────────────────── */
const Icon = ({ d, d2, viewBox = "0 0 24 24" }) => (
  <svg viewBox={viewBox} fill="none" stroke="currentColor" strokeWidth="1.8"
    strokeLinecap="round" strokeLinejoin="round" width="18" height="18">
    <path d={d} />
    {d2 && <path d={d2} />}
  </svg>
);

const ICONS = {
  home:     "M3 9.5L12 3l9 6.5V20a1 1 0 01-1 1H4a1 1 0 01-1-1V9.5z",
  diet:     "M12 2a10 10 0 100 20A10 10 0 0012 2zm0 6v6m-3-3h6",
  exercise: "M13 2L3 14h9l-1 8 10-12h-9l1-8z",
  pill:     "M10.5 6.5l7 7m-3.5-8.5l4 4a5 5 0 01-7 7l-4-4a5 5 0 017-7z",
  moon:     "M21 12.79A9 9 0 1111.21 3a7 7 0 009.79 9.79z",
  drop:     "M12 2.69l5.66 5.66a8 8 0 11-11.31 0L12 2.69z",
  scale:    "M12 3v18M3 9h18M5 21h14M7 9a5 5 0 0010 0",
  chart:    "M18 20V10M12 20V4M6 20v-6",
  file:     "M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8L14 2zm0 0v6h6M9 13h6M9 17h4",
  bot:      "M12 2a4 4 0 014 4v1h1a2 2 0 012 2v8a2 2 0 01-2 2H7a2 2 0 01-2-2V9a2 2 0 012-2h1V6a4 4 0 014-4zm-2 9a1 1 0 100 2 1 1 0 000-2zm4 0a1 1 0 100 2 1 1 0 000-2z",
  user:     "M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2M12 11a4 4 0 100-8 4 4 0 000 8z",
  settings: "M12 15a3 3 0 100-6 3 3 0 000 6zm7.07-1.93l.77-.45a1 1 0 000-1.24l-.77-.45a7 7 0 00-.86-2.07l.13-.88a1 1 0 00-.7-.7l-.88.13a7 7 0 00-2.07-.86L14.17 5a1 1 0 00-1.24 0l-.45.77a7 7 0 00-2.07.86l-.88-.13a1 1 0 00-.7.7l.13.88a7 7 0 00-.86 2.07l-.77.45a1 1 0 000 1.24l.77.45c.2.68.49 1.31.86 2.07l-.13.88a1 1 0 00.7.7l.88-.13c.68.37 1.39.66 2.07.86l.45.77a1 1 0 001.24 0l.45-.77a7 7 0 002.07-.86l.88.13a1 1 0 00.7-.7l-.13-.88c.37-.76.66-1.39.86-2.07z",
  reports:  "M9 17v-2m3 2v-4m3 4v-6M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z",
  calendar: "M8 2v4M16 2v4M3 10h18M5 4h14a2 2 0 012 2v14a2 2 0 01-2 2H5a2 2 0 01-2-2V6a2 2 0 012-2z",
};

const NAV = [
  { section: "MAIN",             items: [
    { label: "Dashboard",        icon: "home",     href: "/dashboard" },
  ]},
  { section: "HEALTH",           items: [
    { label: "Diet Plan",        icon: "diet",     href: "/diet" },
    { label: "Exercise",         icon: "exercise", href: "/exercise" },
    { label: "Medicine Reminder",icon: "pill",     href: "/medicine" },
  ]},
  { section: "TRACKING",         items: [
    { label: "Sleep Tracker",    icon: "moon",     action: "sleep" },
    { label: "Water Tracker",    icon: "drop",     action: "water" },
    { label: "BMI Calculator",   icon: "scale",    action: "bmi" },
    { label: "Analytics",        icon: "reports",  href: "/analytics" },
  ]},
  { section: "MEDICAL",          items: [
    { label: "Medical Reports",  icon: "file",     href: "/medical-reports" },
    { label: "Appointments",     icon: "calendar", href: "/appointments" },
  ]},
  { section: "AI",               items: [
    { label: "AI Assistant",     icon: "bot",      href: "/ai-assistant" },
  ]},
  { section: "ACCOUNT",          items: [
    { label: "Profile",          icon: "user",     href: "/profile" },
    { label: "Settings",         icon: "settings", href: "/settings" },
  ]},
];

export default function Sidebar({ collapsed, toggleSidebar, openBMI, openSleepTracker, openWaterTracker }) {
  const navigate = useNavigate();
  const location = useLocation();

  const handleItem = (item) => {
    if (item.href) return navigate(item.href);
    if (item.action === "bmi")   return openBMI?.();
    if (item.action === "sleep") return openSleepTracker?.();
    if (item.action === "water") return openWaterTracker?.();
  };

  return (
    <div className={`sidebar ${collapsed ? "collapsed" : ""}`}>
      <div className="sidebar-header">
        {!collapsed && <h2 className="sidebar-brand">Heallio</h2>}
        <button onClick={toggleSidebar} className="toggle-btn" aria-label="Toggle sidebar">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
            {collapsed
              ? <path d="M9 18l6-6-6-6"/>
              : <path d="M15 18l-6-6 6-6"/>}
          </svg>
        </button>
      </div>

      <nav className="sidebar-nav">
        {NAV.map(({ section, items }) => (
          <div className="nav-section" key={section}>
            {!collapsed && <p className="section-title">{section}</p>}
            <ul>
              {items.map((item) => {
                const isActive = item.href && location.pathname === item.href;
                return (
                  <li
                    key={item.label}
                    className={`nav-item ${isActive ? "active" : ""}`}
                    title={collapsed ? item.label : ""}
                    onClick={() => handleItem(item)}
                  >
                    <span className="nav-icon">
                      <Icon d={ICONS[item.icon]} />
                    </span>
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
