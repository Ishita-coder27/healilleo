import HamburgerMenu from "./HamburgerMenu";
import "../pages/Dashboard.css";

function DashboardLayout({ title, subtitle, children }) {
  return (
    <div className="app-layout">
      <HamburgerMenu />

      <div className="main-area">
        <h1>{title}</h1>
        <p className="subtitle">{subtitle}</p>

        <div className="content-grid">
          {children}
        </div>
      </div>
    </div>
  );
}

export default DashboardLayout;


