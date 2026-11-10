import os

# the tests use their own small database file, never the real one
os.environ["DATABASE_URL"] = "sqlite:///./test_wallet.db"
