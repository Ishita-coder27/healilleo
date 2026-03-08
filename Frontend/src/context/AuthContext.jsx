import { createContext, useContext, useState, useEffect } from "react";

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user,        setUser]        = useState(null);
  const [token,       setToken]       = useState(null);
  const [isLoggedIn,  setIsLoggedIn]  = useState(false);
  const [loading,     setLoading]     = useState(true); // hydrate from localStorage

  // Hydrate on mount
  useEffect(() => {
    const storedToken = localStorage.getItem("heallio_token");
    const storedUser  = localStorage.getItem("heallio_user");
    if (storedToken && storedUser) {
      setToken(storedToken);
      setUser(JSON.parse(storedUser));
      setIsLoggedIn(true);
    }
    setLoading(false);
  }, []);

  const login = (accessToken, userData) => {
    localStorage.setItem("heallio_token", accessToken);
    localStorage.setItem("heallio_user",  JSON.stringify(userData));
    setToken(accessToken);
    setUser(userData);
    setIsLoggedIn(true);
  };

  const logout = () => {
    localStorage.removeItem("heallio_token");
    localStorage.removeItem("heallio_user");
    setToken(null);
    setUser(null);
    setIsLoggedIn(false);
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