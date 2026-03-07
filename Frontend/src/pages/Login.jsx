import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import "./Login.css";

function Login() {

  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = (e) => {
    e.preventDefault();

    if(email && password){

      localStorage.setItem("user", "true");

      navigate("/dashboard");

    } else {
      alert("Please enter email and password");
    }
  };

  return (

    <div className="login-page">

      <div className="login-card">

        <h1 className="logo">AI Health</h1>

        <p className="tagline">
          Your personal AI powered health companion
        </p>

        <form onSubmit={handleLogin}>

          <input
            type="email"
            placeholder="Email Address"
            value={email}
            onChange={(e)=>setEmail(e.target.value)}
          />

          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e)=>setPassword(e.target.value)}
          />

          <button type="submit">
            Login
          </button>

        </form>

        <p className="footer-text">
          Track your health. Improve your life.
        </p>

      </div>

    </div>
  );
}

export default Login;





