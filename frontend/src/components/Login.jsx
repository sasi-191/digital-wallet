import { useState } from "react";
import { login, register } from "../api.js";

function Login({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isNewUser, setIsNewUser] = useState(false);
  const [message, setMessage] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setMessage("");
    try {
      if (isNewUser) {
        await register(username, password);
      }
      const token = await login(username, password);
      onLogin(token);
    } catch (err) {
      setMessage(err.message);
    }
  }

  return (
    <div className="login-box">
      <h1>Digital Wallet</h1>
      <form onSubmit={handleSubmit}>
        <input placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
        <input placeholder="Password (6 or more letters)" type="password" value={password}
               onChange={(e) => setPassword(e.target.value)} />
        <button type="submit">{isNewUser ? "Create account" : "Log in"}</button>
      </form>
      <p className="switch" onClick={() => setIsNewUser(!isNewUser)}>
        {isNewUser ? "Already have an account? Log in" : "New here? Create an account"}
      </p>
      {message && <p className="error">{message}</p>}
    </div>
  );
}

export default Login;
