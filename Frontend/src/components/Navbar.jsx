import React, { useState } from "react";
import "./Navbar.css";

const NAV_ITEMS = [
  {
    label: "Update Reports",
    icon: "📁",
    dropdown: [
      { icon: "⬆️", label: "Upload New Report",  desc: "Add a new lab or medical report"   },
      { icon: "🗑️", label: "Delete a Report",    desc: "Remove an existing report"         },
      { icon: "📋", label: "View All Reports",   desc: "Browse your full report history"   },
    ],
  },
  {
    label: "Appointments",
    icon: "🗓️",
    dropdown: [
      { icon: "➕", label: "Book Appointment",      desc: "Schedule a new doctor visit"       },
      { icon: "❌", label: "Cancel Appointment",    desc: "Remove an upcoming appointment"    },
      { icon: "📅", label: "View All Appointments", desc: "See your full appointment history" },
    ],
  },
  {
    label: "Medications",
    icon: "💊",
    dropdown: [
      { icon: "➕", label: "Add Medication",      desc: "Log a new medication & schedule"   },
      { icon: "🗑️", label: "Remove Medication",   desc: "Delete a medication from your list" },
      { icon: "📋", label: "View All Medications", desc: "Browse your full medication list"  },
    ],
  },
  { label: "BMI Check",  icon: "📊", href: "#" },
  { label: "Diet Plan",  icon: "🥗", href: "#" },
  { label: "Exercise",   icon: "🏋️", href: "#" },
];

export default function Navbar() {
  const [menuOpen,        setMenuOpen]        = useState(false);
  const [activeDropdown,  setActiveDropdown]  = useState(null);
  const [mobileExpanded,  setMobileExpanded]  = useState(null);

  return (
    <nav className="hn-root">
      <div className="hn-inner">

        {/* ── Logo ── */}
        <a className="hn-logo" href="#">
          <span className="hn-logo-icon">🩺</span>
          <span className="hn-logo-text">Heallio</span>
        </a>

        {/* ── Desktop nav ── */}
        <ul className="hn-links">
          {NAV_ITEMS.map((item) => (
            <li
              key={item.label}
              className={`hn-item ${item.dropdown ? "has-dropdown" : ""}`}
              onMouseEnter={() => item.dropdown && setActiveDropdown(item.label)}
              onMouseLeave={() => item.dropdown && setActiveDropdown(null)}
            >
              <a
                className={`hn-link ${activeDropdown === item.label ? "active" : ""}`}
                href={item.href || "#"}
                onClick={(e) => { if (item.dropdown) e.preventDefault(); }}
              >
                <span className="hn-link-icon">{item.icon}</span>
                {item.label}
                {item.dropdown && (
                  <svg className={`hn-chevron ${activeDropdown === item.label ? "flipped" : ""}`} viewBox="0 0 10 6" fill="none">
                    <path d="M1 1l4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                )}
              </a>

              {item.dropdown && activeDropdown === item.label && (
                <div className="hn-dropdown">
                  {item.dropdown.map((d) => (
                    <a className="hn-dd-item" href="#" key={d.label}>
                      <span className="hn-dd-icon">{d.icon}</span>
                      <div>
                        <div className="hn-dd-label">{d.label}</div>
                        <div className="hn-dd-desc">{d.desc}</div>
                      </div>
                    </a>
                  ))}
                </div>
              )}
            </li>
          ))}
        </ul>

        {/* ── Desktop right ── */}
        <div className="hn-right">
          <div className="hn-search">
            <svg viewBox="0 0 20 20" fill="none">
              <circle cx="8.5" cy="8.5" r="5.5" stroke="currentColor" strokeWidth="1.6"/>
              <path d="M13 13l3.5 3.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/>
            </svg>
            <input placeholder="Search…" />
          </div>
          <button className="hn-signin">Sign In</button>
          {/* <button className="hn-cta">Get Started Free →</button> */}
          <div className="hn-avatar">S</div>
        </div>

        {/* ── Hamburger ── */}
        <button
          className={`hn-hamburger ${menuOpen ? "open" : ""}`}
          onClick={() => setMenuOpen(!menuOpen)}
          aria-label="Toggle menu"
        >
          <span /><span /><span />
        </button>
      </div>

      {/* ── Mobile menu ── */}
      {menuOpen && (
        <div className="hn-mobile-menu">
          {NAV_ITEMS.map((item) => (
            <div key={item.label} className="hn-mobile-item">
              <button
                className="hn-mobile-link"
                onClick={() =>
                  item.dropdown
                    ? setMobileExpanded((p) => (p === item.label ? null : item.label))
                    : setMenuOpen(false)
                }
              >
                <span>{item.icon}</span>
                {item.label}
                {item.dropdown && (
                  <svg
                    className={`hn-chevron ${mobileExpanded === item.label ? "flipped" : ""}`}
                    viewBox="0 0 10 6" fill="none"
                  >
                    <path d="M1 1l4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                )}
              </button>
              {item.dropdown && mobileExpanded === item.label && (
                <div className="hn-mobile-dropdown">
                  {item.dropdown.map((d) => (
                    <a className="hn-mobile-dd-item" href="#" key={d.label}>
                      <span>{d.icon}</span> {d.label}
                    </a>
                  ))}
                </div>
              )}
            </div>
          ))}
          <div className="hn-mobile-actions">
            <button className="hn-signin full">Sign In</button>
            <button className="hn-cta full">Get Started Free →</button>
          </div>
        </div>
      )}
    </nav>
  );
}