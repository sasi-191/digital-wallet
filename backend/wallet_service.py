from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from db_models import LedgerEntry, Transaction, User, Wallet


def rupees_to_paise(amount):
    return int(round(amount * 100))


def paise_to_rupees(paise):
    return paise / 100


def get_user_wallet(db, user):
    return db.query(Wallet).filter(Wallet.user_id == user.id).first()


def get_bank_wallet(db):
    """The wallet that deposits come from. Its balance goes below zero, like a real bank's books."""
    bank = db.query(Wallet).filter(Wallet.name == "BANK", Wallet.user_id.is_(None)).first()
    if bank is None:
        bank = Wallet(name="BANK", user_id=None, balance_paise=0)
        db.add(bank)
        db.commit()
    return bank


def find_earlier_request(db, idempotency_key):
    if not idempotency_key:
        return None
    return db.query(Transaction).filter(Transaction.idempotency_key == idempotency_key).first()


def move_money(db, kind, from_wallet, to_wallet, amount_paise, note, idempotency_key):
    """Moves money and writes both ledger lines. Everything is saved together, or nothing is."""
    from_wallet.balance_paise = from_wallet.balance_paise - amount_paise
    to_wallet.balance_paise = to_wallet.balance_paise + amount_paise

    transaction = Transaction(kind=kind, from_wallet_id=from_wallet.id, to_wallet_id=to_wallet.id,
                              amount_paise=amount_paise, note=note, idempotency_key=idempotency_key)
    db.add(transaction)
    db.flush()      # gives the transaction its id, without saving yet

    db.add(LedgerEntry(transaction_id=transaction.id, wallet_id=from_wallet.id,
                       amount_paise=-amount_paise, balance_after_paise=from_wallet.balance_paise))
    db.add(LedgerEntry(transaction_id=transaction.id, wallet_id=to_wallet.id,
                       amount_paise=amount_paise, balance_after_paise=to_wallet.balance_paise))
    try:
        db.commit()
    except IntegrityError:
        # two copies of the same request arrived at the same time: keep the first one only
        db.rollback()
        return find_earlier_request(db, idempotency_key)
    return transaction


def deposit(db, user, amount, idempotency_key=None):
    earlier = find_earlier_request(db, idempotency_key)
    if earlier is not None:
        return earlier

    bank = get_bank_wallet(db)
    wallet = get_user_wallet(db, user)
    return move_money(db, "DEPOSIT", bank, wallet, rupees_to_paise(amount), "Added money", idempotency_key)


def transfer(db, sender, to_username, amount, note="", idempotency_key=None):
    earlier = find_earlier_request(db, idempotency_key)
    if earlier is not None:
        return earlier

    receiver = db.query(User).filter(User.username == to_username).first()
    if receiver is None:
        raise HTTPException(status_code=404, detail="No user called " + to_username)
    if receiver.id == sender.id:
        raise HTTPException(status_code=400, detail="You cannot send money to yourself")

    sender_wallet = get_user_wallet(db, sender)
    receiver_wallet = get_user_wallet(db, receiver)

    # lock both wallet rows until we commit, so two transfers at the same time cannot
    # both spend the same money. Locking in id order stops two transfers waiting for each other.
    wallet_ids = sorted([sender_wallet.id, receiver_wallet.id])
    db.query(Wallet).filter(Wallet.id.in_(wallet_ids)).order_by(Wallet.id).with_for_update().all()
    db.refresh(sender_wallet)

    amount_paise = rupees_to_paise(amount)
    if sender_wallet.balance_paise < amount_paise:
        db.rollback()
        raise HTTPException(status_code=400, detail="Not enough balance")

    return move_money(db, "TRANSFER", sender_wallet, receiver_wallet, amount_paise, note, idempotency_key)


def history(db, user, kind=None, limit=50):
    """The user's own ledger lines, newest first, with the other person's name."""
    wallet = get_user_wallet(db, user)
    query = db.query(LedgerEntry, Transaction).join(Transaction, LedgerEntry.transaction_id == Transaction.id)
    query = query.filter(LedgerEntry.wallet_id == wallet.id)
    if kind:
        query = query.filter(Transaction.kind == kind)
    rows = query.order_by(LedgerEntry.id.desc()).limit(limit).all()

    result = []
    for entry, transaction in rows:
        if entry.amount_paise > 0:
            other_wallet_id = transaction.from_wallet_id
        else:
            other_wallet_id = transaction.to_wallet_id
        other_wallet = db.query(Wallet).filter(Wallet.id == other_wallet_id).first()

        result.append({
            "date": transaction.created_at.strftime("%Y-%m-%d %H:%M"),
            "type": transaction.kind,
            "amount": paise_to_rupees(entry.amount_paise),
            "other_party": other_wallet.name,
            "note": transaction.note,
            "balance_after": paise_to_rupees(entry.balance_after_paise),
        })
    return result


def ledger_check(db):
    """Checks that the books are correct: every line adds up to zero, and every balance equals the sum of its own lines."""
    total = db.query(func.coalesce(func.sum(LedgerEntry.amount_paise), 0)).scalar()

    wrong_wallets = []
    for wallet in db.query(Wallet).all():
        sum_of_lines = db.query(func.coalesce(func.sum(LedgerEntry.amount_paise), 0)) \
            .filter(LedgerEntry.wallet_id == wallet.id).scalar()
        if sum_of_lines != wallet.balance_paise:
            wrong_wallets.append(wallet.name)

    return {"all_lines_add_up_to_zero": total == 0, "wallets_that_do_not_match": wrong_wallets}
