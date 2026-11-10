from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from db_models import User
from rate_limit import check_transfer_limit
from schemas import DepositRequest, TransferRequest
from wallet_service import deposit, get_user_wallet, history, ledger_check, paise_to_rupees, transfer

router = APIRouter(tags=["wallet"])


def transaction_to_dict(transaction):
    return {
        "transaction_id": transaction.id,
        "type": transaction.kind,
        "amount": paise_to_rupees(transaction.amount_paise),
        "date": transaction.created_at.strftime("%Y-%m-%d %H:%M"),
    }


@router.get("/wallet")
def my_wallet(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    wallet = get_user_wallet(db, user)
    return {"username": user.username, "balance": paise_to_rupees(wallet.balance_paise)}


@router.post("/wallet/deposit")
def add_money(request: DepositRequest, idempotency_key: str = Header(default=None),
              user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    transaction = deposit(db, user, request.amount, idempotency_key)
    return transaction_to_dict(transaction)


@router.post("/transfers")
def send_money(request: TransferRequest, idempotency_key: str = Header(default=None),
               user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_transfer_limit(user.username)
    transaction = transfer(db, user, request.to_username, request.amount, request.note, idempotency_key)
    return transaction_to_dict(transaction)


@router.get("/transactions")
def my_transactions(kind: str = None, limit: int = 50,
                    user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return history(db, user, kind, limit)


@router.get("/ledger-check")
def check_books(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return ledger_check(db)
