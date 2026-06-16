import { Routes, Route } from "react-router-dom";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import MedicalReports from "./pages/MedicalReports";
import Analytics from "./pages/Analytics";
import AIAssistant from "./pages/AIAssistant";
import MedicineSchedule from "./pages/MedicineSchedule";
import DietPlan from "./pages/DietPlan";
import Exercise from "./pages/Exercise";
import Profile from "./pages/Profile";
import Settings from "./pages/Settings";
import Appointments from "./pages/Appointments";
import ProtectedRoute from "./components/ProtectedRoute";

function App() {
  return (
    <Routes>
      <Route path="/"        element={<Login />} />
      <Route path="/register" element={<Register />} />

      <Route path="/dashboard"      element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
      <Route path="/medical-reports" element={<ProtectedRoute><MedicalReports /></ProtectedRoute>} />
      <Route path="/analytics"      element={<ProtectedRoute><Analytics /></ProtectedRoute>} />
      <Route path="/ai-assistant"   element={<ProtectedRoute><AIAssistant /></ProtectedRoute>} />
      <Route path="/medicine"       element={<ProtectedRoute><MedicineSchedule /></ProtectedRoute>} />
      <Route path="/diet"           element={<ProtectedRoute><DietPlan /></ProtectedRoute>} />
      <Route path="/exercise"       element={<ProtectedRoute><Exercise /></ProtectedRoute>} />
      <Route path="/profile"        element={<ProtectedRoute><Profile /></ProtectedRoute>} />
      <Route path="/settings"       element={<ProtectedRoute><Settings /></ProtectedRoute>} />
      <Route path="/appointments"   element={<ProtectedRoute><Appointments /></ProtectedRoute>} />
    </Routes>
  );
}

export default App;
