import pytest
from fastapi.testclient import TestClient

import rate_limit
from database import Base, engine
from main import app


@pytest.fixture
def client():
    # a clean database and a clean rate limit for every test
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    rate_limit.recent_transfers.clear()
    with TestClient(app) as test_client:
        yield test_client


def sign_up_and_log_in(client, username):
    client.post("/register", json={"username": username, "password": "secret123"})
    answer = client.post("/login", data={"username": username, "password": "secret123"})
    return {"Authorization": "Bearer " + answer.json()["access_token"]}


def balance(client, headers):
    return client.get("/wallet", headers=headers).json()["balance"]


def test_register_twice_is_refused(client):
    first = client.post("/register", json={"username": "ravi", "password": "secret123"})
    second = client.post("/register", json={"username": "ravi", "password": "secret123"})
    assert first.status_code == 201
    assert second.status_code == 400


def test_wallet_needs_login(client):
    assert client.get("/wallet").status_code == 401


def test_deposit_and_transfer(client):
    ravi = sign_up_and_log_in(client, "ravi")
    sita = sign_up_and_log_in(client, "sita")

    client.post("/wallet/deposit", json={"amount": 1000}, headers=ravi)
    answer = client.post("/transfers", json={"to_username": "sita", "amount": 250.50, "note": "lunch"},
                         headers=ravi)
    assert answer.status_code == 200
    assert balance(client, ravi) == 749.50
    assert balance(client, sita) == 250.50


def test_not_enough_balance(client):
    ravi = sign_up_and_log_in(client, "ravi")
    sign_up_and_log_in(client, "sita")
    answer = client.post("/transfers", json={"to_username": "sita", "amount": 10}, headers=ravi)
    assert answer.status_code == 400


def test_cannot_send_to_yourself(client):
    ravi = sign_up_and_log_in(client, "ravi")
    client.post("/wallet/deposit", json={"amount": 100}, headers=ravi)
    answer = client.post("/transfers", json={"to_username": "ravi", "amount": 10}, headers=ravi)
    assert answer.status_code == 400


def test_same_request_twice_moves_money_once(client):
    ravi = sign_up_and_log_in(client, "ravi")
    sign_up_and_log_in(client, "sita")
    client.post("/wallet/deposit", json={"amount": 1000}, headers=ravi)

    headers = dict(ravi)
    headers["Idempotency-Key"] = "payment-001"
    first = client.post("/transfers", json={"to_username": "sita", "amount": 100}, headers=headers)
    second = client.post("/transfers", json={"to_username": "sita", "amount": 100}, headers=headers)

    assert first.json()["transaction_id"] == second.json()["transaction_id"]
    assert balance(client, ravi) == 900


def test_books_always_balance(client):
    ravi = sign_up_and_log_in(client, "ravi")
    sign_up_and_log_in(client, "sita")
    client.post("/wallet/deposit", json={"amount": 500}, headers=ravi)
    client.post("/transfers", json={"to_username": "sita", "amount": 120}, headers=ravi)

    check = client.get("/ledger-check", headers=ravi).json()
    assert check["all_lines_add_up_to_zero"] is True
    assert check["wallets_that_do_not_match"] == []


def test_too_many_transfers(client):
    ravi = sign_up_and_log_in(client, "ravi")
    sign_up_and_log_in(client, "sita")
    client.post("/wallet/deposit", json={"amount": 1000}, headers=ravi)

    codes = []
    for number in range(6):
        answer = client.post("/transfers", json={"to_username": "sita", "amount": 1}, headers=ravi)
        codes.append(answer.status_code)
    assert codes[:5] == [200, 200, 200, 200, 200]
    assert codes[5] == 429


def test_history_shows_both_sides(client):
    ravi = sign_up_and_log_in(client, "ravi")
    sita = sign_up_and_log_in(client, "sita")
    client.post("/wallet/deposit", json={"amount": 300}, headers=ravi)
    client.post("/transfers", json={"to_username": "sita", "amount": 100, "note": "books"}, headers=ravi)

    ravi_history = client.get("/transactions", headers=ravi).json()
    sita_history = client.get("/transactions", headers=sita).json()
    assert ravi_history[0]["amount"] == -100
    assert sita_history[0]["amount"] == 100
    assert sita_history[0]["other_party"] == "ravi"
