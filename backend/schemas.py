from pydantic import BaseModel, Field

from config import MAX_AMOUNT


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=20)
    password: str = Field(min_length=6)


class DepositRequest(BaseModel):
    amount: float = Field(gt=0, le=MAX_AMOUNT)      # in rupees


class TransferRequest(BaseModel):
    to_username: str
    amount: float = Field(gt=0, le=MAX_AMOUNT)      # in rupees
    note: str = Field(default="", max_length=100)
