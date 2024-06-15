from datetime import datetime
from pydantic import BaseModel


class Transfer(BaseModel):
    from_bank: str
    from_account: str
    to_bank: str
    to_account: str
    amount: int
    transfer_date: datetime


class NewTransfer(BaseModel):
    to_bank: str
    to_account: str
    amount: int
