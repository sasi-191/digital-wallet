# Digital Wallet

A small wallet app like a mini Paytm. Create an account, add money, send money to other users
and see your history.

## Features

- Register and login
- Add money and send money to other users
- Transaction history
- Money is stored in paise (whole numbers) so there are no decimal errors
- Double entry ledger: every transaction writes a minus line and a plus line, /ledger-check checks the totals
- Idempotency key: the same request sent twice does not pay twice
- Row locking so two transfers at the same time cannot spend the same money
- Max 5 transfers per minute per user

## Tech

Python, FastAPI, SQLAlchemy, PostgreSQL / SQLite, React, Docker

## Run

Backend:

```
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn main:app --reload
```

Frontend:

```
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

Tests: `cd backend` then `pytest`
