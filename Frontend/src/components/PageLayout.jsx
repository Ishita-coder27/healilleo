import React, { useState } from "react";
import Sidebar from "./Sidebar";
import Navbar from "./Navbar";
import BMICalculator from "./BMICalculator";
import SleepTracker from "./SleepTracker";
import WaterTracker from "./WaterTracker";
import "../pages/Dashboard.css";

export default function PageLayout({ children }) {
  const [collapsed,  setCollapsed]  = useState(false);
  const [bmiOpen,    setBmiOpen]    = useState(false);
  const [sleepOpen,  setSleepOpen]  = useState(false);
  const [waterOpen,  setWaterOpen]  = useState(false);

  return (
    <div className="heallio-layout">
      <Sidebar
        collapsed={collapsed}
        toggleSidebar={() => setCollapsed((c) => !c)}
        openBMI={()          => setBmiOpen(true)}
        openSleepTracker={()  => setSleepOpen(true)}
        openWaterTracker={()  => setWaterOpen(true)}
      />
      <div className={`heallio-main ${collapsed ? "sidebar-collapsed" : ""}`}>
        <Navbar
          openBMI={()          => setBmiOpen(true)}
          openSleepTracker={()  => setSleepOpen(true)}
          openWaterTracker={()  => setWaterOpen(true)}
        />
        <div className="heallio-content">{children}</div>
      </div>

      <BMICalculator
        open={bmiOpen}
        onClose={() => setBmiOpen(false)}
      />
      <SleepTracker
        open={sleepOpen}
        onClose={() => setSleepOpen(false)}
        onAskLLM={() => {}}
      />
      <WaterTracker
        open={waterOpen}
        onClose={() => setWaterOpen(false)}
        onAskLLM={() => {}}
      />
    </div>
  );
}
