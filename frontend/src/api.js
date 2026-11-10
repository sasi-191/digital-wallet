const API_URL = "http://localhost:8000";

export async function register(username, password) {
  const response = await fetch(API_URL + "/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username: username, password: password }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(readError(data));
  }
  return data;
}

export async function login(username, password) {
  const form = new URLSearchParams();
  form.append("username", username);
  form.append("password", password);

  const response = await fetch(API_URL + "/login", { method: "POST", body: form });
  if (!response.ok) {
    throw new Error("Wrong username or password");
  }
  const data = await response.json();
  return data.access_token;
}

export async function getData(path, token) {
  const response = await fetch(API_URL + path, {
    headers: { Authorization: "Bearer " + token },
  });
  if (response.status === 401) {
    throw new Error("LOGIN_AGAIN");
  }
  return response.json();
}

// every money request gets its own unique key, so a double click never pays twice
export async function sendMoneyRequest(path, token, body) {
  const response = await fetch(API_URL + path, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: "Bearer " + token,
      "Idempotency-Key": crypto.randomUUID(),
    },
    body: JSON.stringify(body),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(readError(data));
  }
  return data;
}

// FastAPI sends errors as text, or as a list when a field is wrong
function readError(data) {
  if (typeof data.detail === "string") {
    return data.detail;
  }
  return "Please check the values you typed";
}
