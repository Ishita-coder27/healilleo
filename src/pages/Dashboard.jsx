import React from "react";
import Sidebar from "../components/Sidebar";
import Lottie from "lottie-react";
import healthAnimation from "../assets/health-animation.json";
import "./Dashboard.css";
function Dashboard() {
  return (
    <div style={{display:"flex"}}>

      <Sidebar />

      <div style={{flex:1, textAlign:"center", padding:"40px"}}>

        <h1 className="moving-heading">Welcome to AI Health Dashboard</h1>
        
        <div style={{width:"400px", margin:"auto"}}>
          <Lottie animationData={healthAnimation} loop={true} />
        </div>

      </div>

    </div>
  );
}

export default Dashboard;