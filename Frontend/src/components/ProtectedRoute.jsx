import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function ProtectedRoute({ children }) {
  const { isLoggedIn, loading } = useAuth();

  if (loading) {
    return (
      <div style={{
        height: "100vh", display: "flex",
        alignItems: "center", justifyContent: "center",
        background: "#0b1f3a", color: "white", fontSize: "16px"
      }}>
        Loading…
      </div>
    );
  }

  return isLoggedIn ? children : <Navigate to="/" replace />;
}