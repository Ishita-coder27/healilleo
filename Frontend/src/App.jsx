import { Routes, Route } from "react-router-dom";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import MedicalReports from "./pages/MedicalReports";
import ProtectedRoute from "./components/ProtectedRoute";

function App() {
  return (
    <Routes>
      <Route path="/"          element={<Login />} />
      <Route path="/register"  element={<Register />} />
<Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
<Route path="/medical-reports" element={
  <ProtectedRoute>
    <MedicalReports />
  </ProtectedRoute>
} />
    </Routes>
  );
}

export default App;