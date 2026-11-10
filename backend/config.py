import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./wallet.db")
SECRET_KEY = os.getenv("SECRET_KEY", "please-change-this-secret")
ALGORITHM = "HS256"
TOKEN_MINUTES = 60

# limits
MAX_AMOUNT = 100000             # Rs 1,00,000 at most per deposit or transfer
TRANSFERS_PER_MINUTE = 5        # a user can send money at most 5 times a minute
