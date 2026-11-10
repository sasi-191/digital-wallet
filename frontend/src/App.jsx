import { useState } from "react";
import Login from "./components/Login.jsx";
import Wallet from "./components/Wallet.jsx";

function App() {
  const [token, setToken] = useState(localStorage.getItem("token"));

  function handleLogin(newToken) {
    localStorage.setItem("token", newToken);
    setToken(newToken);
  }

  function handleLogout() {
    localStorage.removeItem("token");
    setToken(null);
  }

  if (!token) {
    return <Login onLogin={handleLogin} />;
  }
  return <Wallet token={token} onLogout={handleLogout} />;
}

export default App;
