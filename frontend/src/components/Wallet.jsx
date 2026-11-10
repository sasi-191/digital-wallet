import { useEffect, useState } from "react";
import { getData, sendMoneyRequest } from "../api.js";

function Wallet({ token, onLogout }) {
  const [wallet, setWallet] = useState(null);
  const [history, setHistory] = useState([]);
  const [depositAmount, setDepositAmount] = useState("");
  const [toUsername, setToUsername] = useState("");
  const [sendAmount, setSendAmount] = useState("");
  const [note, setNote] = useState("");
  const [message, setMessage] = useState("");

  async function loadWallet() {
    try {
      setWallet(await getData("/wallet", token));
      setHistory(await getData("/transactions", token));
    } catch (err) {
      if (err.message === "LOGIN_AGAIN") {
        onLogout();
      }
    }
  }

  useEffect(() => {
    loadWallet();
  }, []);

  async function addMoney(event) {
    event.preventDefault();
    try {
      await sendMoneyRequest("/wallet/deposit", token, { amount: Number(depositAmount) });
      setMessage("Added Rs " + depositAmount);
      setDepositAmount("");
      loadWallet();
    } catch (err) {
      setMessage(err.message);
    }
  }

  async function sendMoney(event) {
    event.preventDefault();
    try {
      await sendMoneyRequest("/transfers", token,
        { to_username: toUsername, amount: Number(sendAmount), note: note });
      setMessage("Sent Rs " + sendAmount + " to " + toUsername);
      setSendAmount("");
      setNote("");
      loadWallet();
    } catch (err) {
      setMessage(err.message);
    }
  }

  if (!wallet) {
    return <p>Loading...</p>;
  }

  return (
    <div className="page">
      <header>
        <h1>Hello, {wallet.username}</h1>
        <button onClick={onLogout}>Log out</button>
      </header>

      <div className="balance">Balance<b>Rs {wallet.balance.toFixed(2)}</b></div>
      {message && <p className="message">{message}</p>}

      <div className="forms">
        <form onSubmit={addMoney}>
          <h2>Add money</h2>
          <input type="number" step="0.01" placeholder="Amount" value={depositAmount}
                 onChange={(e) => setDepositAmount(e.target.value)} />
          <button type="submit">Add</button>
        </form>

        <form onSubmit={sendMoney}>
          <h2>Send money</h2>
          <input placeholder="To (username)" value={toUsername} onChange={(e) => setToUsername(e.target.value)} />
          <input type="number" step="0.01" placeholder="Amount" value={sendAmount}
                 onChange={(e) => setSendAmount(e.target.value)} />
          <input placeholder="Note (optional)" value={note} onChange={(e) => setNote(e.target.value)} />
          <button type="submit">Send</button>
        </form>
      </div>

      <h2>History</h2>
      {history.length === 0 ? (
        <p className="empty">No transactions yet.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Date</th><th>Type</th><th>With</th><th>Note</th><th>Amount</th><th>Balance after</th>
            </tr>
          </thead>
          <tbody>
            {history.map((row, index) => (
              <tr key={index}>
                <td>{row.date}</td>
                <td>{row.type}</td>
                <td>{row.other_party}</td>
                <td>{row.note}</td>
                <td className={row.amount < 0 ? "minus" : "plus"}>{row.amount.toFixed(2)}</td>
                <td>{row.balance_after.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default Wallet;
