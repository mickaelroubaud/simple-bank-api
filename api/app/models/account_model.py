from pydantic import BaseModel


class Account(BaseModel):
    user: str
    bank: str
    account_number: str
    balance: int | None = None
