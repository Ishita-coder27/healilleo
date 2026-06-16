import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./Login.css";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";


export default function Register() {
  const navigate  = useNavigate();
  const { login } = useAuth();

  const [form,    setForm]    = useState({ name: "", email: "", password: "", confirm: "", phone_number: "", age: "" });
  const [error,   setError]   = useState("");
  const [loading, setLoading] = useState(false);

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  const handleRegister = async (e) => {
    e.preventDefault();
    setError("");

    if (!form.name || !form.email || !form.password || !form.phone_number) {
      setError("Name, email, password and phone are required."); return;
    }
    if (form.password !== form.confirm) {
      setError("Passwords do not match."); return;
    }
    if (form.password.length < 6) {
      setError("Password must be at least 6 characters."); return;
    }

    setLoading(true);
    try {
      const res  = await fetch(`${API}/auth/register`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name:         form.name,
          email:        form.email,
          password:     form.password,
          phone_number: form.phone_number,
          age:          form.age ? parseInt(form.age) : null,
        }),
      });
      const data = await res.json();
      if (!res.ok) { setError(data.detail || "Registration failed."); return; }
      login(data.access_token, data.user);
      navigate("/dashboard");
    } catch {
      setError("Cannot reach server. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card login-card-wide">

        <div className="login-logo">
          <span className="login-logo-icon">🩺</span>
          <h1 className="login-logo-text">Heallio</h1>
        </div>
        <p className="login-tagline">Create your health account</p>

        {error && <div className="login-error">{error}</div>}

        <form onSubmit={handleRegister} className="login-form">

          <div className="login-row-2">
            <div className="login-field">
              <label>Full Name *</label>
              <input placeholder="John Doe" value={form.name} onChange={update("name")} disabled={loading} />
            </div>
            <div className="login-field">
              <label>Age</label>
              <input type="number" placeholder="25" value={form.age} onChange={update("age")} disabled={loading} />
            </div>
          </div>

          <div className="login-field">
            <label>Email Address *</label>
            <input type="email" placeholder="you@example.com" value={form.email} onChange={update("email")} disabled={loading} />
          </div>

          <div className="login-field">
            <label>Phone Number *</label>
            <input type="tel" placeholder="+91 98765 43210" value={form.phone_number} onChange={update("phone_number")} disabled={loading} />
          </div>

          <div className="login-row-2">
            <div className="login-field">
              <label>Password *</label>
              <input type="password" placeholder="••••••••" value={form.password} onChange={update("password")} disabled={loading} />
            </div>
            <div className="login-field">
              <label>Confirm Password *</label>
              <input type="password" placeholder="••••••••" value={form.confirm} onChange={update("confirm")} disabled={loading} />
            </div>
          </div>

          <button type="submit" className="login-btn-primary" disabled={loading}>
            {loading ? <span className="login-spinner" /> : "Create Account"}
          </button>
        </form>

        <p className="login-footer">
          Already have an account? <Link to="/">Sign in</Link>
        </p>
      </div>
    </div>
  );
}