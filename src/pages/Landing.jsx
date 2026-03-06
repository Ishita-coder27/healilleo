import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import "../styles/landing.css";


export default function Landing() {
  const navigate = useNavigate();

  return (
    <div className="landing-container">
      <motion.div
        className="landing-content"
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
      >
        <h1>
          AI Health <span>Assistant</span>
        </h1>

        <p>
          Your personal AI-powered healthcare companion for smarter
          reports, medicine guidance, and healthy living.
        </p>

        <div className="landing-buttons">
          <button
            className="btn primary"
            onClick={() => navigate("/register")}
          >
            Get Started
          </button>

          <button
            className="btn secondary"
            onClick={() => navigate("/login")}
          >
            Login
          </button>
        </div>
      </motion.div>
    </div>
  );
}

