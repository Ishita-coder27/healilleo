import { Routes, Route } from "react-router-dom";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import MedicalReports from "./pages/MedicalReports";
import ProtectedRoute from "./components/ProtectedRoute";
import { ContextProvider } from "./context/ContextProvider"
// ... other imports

// export default function App() {
//   return (
//     <ContextProvider>
//       {/* your existing router/routes here */}
//     </ContextProvider>
//   )
// }

function App() {
  return (<ContextProvider>
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
  </ContextProvider>);
}

export default App;