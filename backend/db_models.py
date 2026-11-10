from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Wallet(Base):
    """Every user has one wallet. One extra wallet called BANK is where deposits come from."""
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=True)
    name = Column(String, nullable=False)
    balance_paise = Column(Integer, nullable=False, default=0)


class Transaction(Base):
    """One money movement: a deposit or a transfer."""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    kind = Column(String, nullable=False)                 # "DEPOSIT" or "TRANSFER"
    from_wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=False)
    to_wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=False)
    amount_paise = Column(Integer, nullable=False)
    note = Column(String)
    # the same key sent twice means "the same request": we never move the money twice
    idempotency_key = Column(String, unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class LedgerEntry(Base):
    """Double-entry bookkeeping: every transaction writes two lines, a minus and a plus."""
    __tablename__ = "ledger_entries"

    id = Column(Integer, primary_key=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)
    wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=False)
    amount_paise = Column(Integer, nullable=False)        # minus = money out, plus = money in
    balance_after_paise = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
