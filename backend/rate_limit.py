import time

from fastapi import HTTPException

from config import TRANSFERS_PER_MINUTE

recent_transfers = {}       # username -> list of times (in seconds) of their recent transfers


def check_transfer_limit(username):
    now = time.time()
    times = recent_transfers.get(username, [])

    # keep only the transfers of the last 60 seconds
    times = [moment for moment in times if now - moment < 60]

    if len(times) >= TRANSFERS_PER_MINUTE:
        raise HTTPException(status_code=429, detail="Too many transfers. Please wait a minute.")

    times.append(now)
    recent_transfers[username] = times
