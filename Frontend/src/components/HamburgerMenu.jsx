import { useState } from "react";
import { Link } from "react-router-dom";
import "../styles/menu.css";

function HamburgerMenu() {
  const [open, setOpen] = useState(false);

  return (
    <>
      {/* Menu Icon */}
      <div className="menu-icon" onClick={() => setOpen(!open)}>
        ☰
      </div>

      {/* Overlay */}
      {open && <div className="overlay" onClick={() => setOpen(false)}></div>}

      {/* Sidebar Menu */}
      <div className={`side-menu ${open ? "open" : ""}`}>
        <h2>AI Health</h2>

        <Link to="/dashboard" onClick={() => setOpen(false)}>Dashboard</Link>
        <Link to="/reports" onClick={() => setOpen(false)}>Medical Reports</Link>
        <Link to="/medicine" onClick={() => setOpen(false)}>Medicine Schedule</Link>
        <Link to="/diet" onClick={() => setOpen(false)}>Diet & Exercise</Link>
      </div>
    </>
  );
}

export default HamburgerMenu;
