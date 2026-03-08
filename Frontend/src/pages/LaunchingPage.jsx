import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import "../styles/landing.css";


export default function LaunchingPage() {
  const navigate = useNavigate();

  return (
    <div className="landing-container">
      {/* NAVBAR */}
      <nav className="navbar">
        <h2 className="logo">AI Health</h2>
        <div>
          <button onClick={() => navigate("/login")}>Login</button>
          <button className="register-btn" onClick={() => navigate("/register")}>
            Register
          </button>
        </div>
      </nav>

      {/* HERO SECTION */}
      <div className="hero">
        <motion.h1
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
        >
          Your AI-Powered Personal Health Assistant
        </motion.h1>

        <p>
          Upload medical reports, track medicines, follow AI-generated
          diet & exercise plans, and chat with an intelligent health assistant.
        </p>

        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
          className="hero-btn"
          onClick={() => navigate("/register")}
        >
          Get Started
        </motion.button>
      </div>
    </div>
  );
}

