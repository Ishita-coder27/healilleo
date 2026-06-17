import { createContext, useContext, useState, useEffect, useRef } from "react";

const AuthContext = createContext();
const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function requestNotificationPermission() {
  if (!("Notification" in window)) return false;
  if (Notification.permission === "granted") return true;
  if (Notification.permission === "denied") return false;
  const result = await Notification.requestPermission();
  return result === "granted";
}

function fireNotification(title, body) {
  if (Notification.permission !== "granted") return;
  new Notification(title, { body, icon: "/favicon.ico" });
}

export function AuthProvider({ children }) {
  const [user,       setUser]       = useState(null);
  const [token,      setToken]      = useState(null);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [loading,    setLoading]    = useState(true);

  const pollRef     = useRef(null);
  const notifiedRef = useRef(new Set()); // ← moved here, at the component level

  const startReminderPolling = (accessToken) => {
    if (pollRef.current) clearInterval(pollRef.current);

    const poll = async () => {
      try {
        const apptRes = await fetch(`${API}/appointments/reminders/due`, {
          headers: { Authorization: `Bearer ${accessToken}` },
        });
        if (apptRes.ok) {
          const appts = await apptRes.json();
          appts.forEach((a) => {
            if (notifiedRef.current.has(`appt-${a.id}`)) return;
            notifiedRef.current.add(`appt-${a.id}`);
            const time = new Date(a.appointment_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
            fireNotification(
              "🗓️ Upcoming Appointment",
              `${a.doctor_name}${a.clinic_name ? ` at ${a.clinic_name}` : ""} — in 1 hour (${time})`
            );
          });
        }

        const medRes = await fetch(`${API}/medications/reminders/due`, {
          headers: { Authorization: `Bearer ${accessToken}` },
        });
        if (medRes.ok) {
          const meds = await medRes.json();
          meds.forEach((m) => {
            if (notifiedRef.current.has(`med-${m.id}`)) return;
            notifiedRef.current.add(`med-${m.id}`);
            fireNotification(
              "💊 Medication Reminder",
              `Time to take ${m.medication_name}${m.dosage ? ` (${m.dosage})` : ""} — due in 15 minutes`
            );
          });
        }
      } catch { }
    };

    poll();
    pollRef.current = setInterval(poll, 30_000);
  };

  const stopReminderPolling = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  };

  // ── Hydrate on mount ──
  useEffect(() => {
    const storedToken = localStorage.getItem("heallio_token");
    const storedUser  = localStorage.getItem("heallio_user");
    if (storedToken && storedUser) {
      setToken(storedToken);
      setUser(JSON.parse(storedUser));
      setIsLoggedIn(true);
      requestNotificationPermission().then((granted) => {
        if (granted) startReminderPolling(storedToken);
      });
    }
    setLoading(false);
    return () => stopReminderPolling();
  }, []);

  const login = async (accessToken, userData) => {
    localStorage.setItem("heallio_token", accessToken);
    localStorage.setItem("heallio_user",  JSON.stringify(userData));
    setToken(accessToken);
    setUser(userData);
    setIsLoggedIn(true);
    const granted = await requestNotificationPermission();
    if (granted) startReminderPolling(accessToken);
  };

  const logout = () => {
    localStorage.removeItem("heallio_token");
    localStorage.removeItem("heallio_user");
    setToken(null);
    setUser(null);
    setIsLoggedIn(false);
    notifiedRef.current.clear();
    stopReminderPolling();
  };

  return (
    <AuthContext.Provider value={{ user, token, isLoggedIn, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}