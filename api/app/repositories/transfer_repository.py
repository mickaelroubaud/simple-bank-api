from datetime import datetime

from app.exceptions.low_balance_exception import LowBalanceException
from app.models.transfer_model import Transfer

fake_transfer_db = [
    {
        "from_bank": "12-34-56",
        "from_account": "11111111",
        "to_bank": "33-01-02",
        "to_account": "123456",
        "amount": 100,
        "transfer_date": datetime.strptime("2024-03-31 03:00:00", "%Y-%m-%d %H:%M:%S"),
    },
    {
        "from_bank": "33-01-02",
        "from_account": "123456",
        "to_bank": "11-11-22",
        "to_account": "009090",
        "amount": 33,
        "transfer_date": datetime.strptime("2024-03-31 06:00:00", "%Y-%m-%d %H:%M:%S"),
    },
    {
        "from_bank": "33-01-02",
        "from_account": "223345",
        "to_bank": "33-01-02",
        "to_account": "123457",
        "amount": 100,
        "transfer_date": datetime.strptime("2024-03-28 06:00:00", "%Y-%m-%d %H:%M:%S"),
    },
]


class TransferRepository:
    @staticmethod
    def list(
        bank: str,
        account_number: str,
        from_date: datetime = None,
        to_date: datetime = None,
    ) -> list[Transfer]:
        transfers = []
        for transfer in fake_transfer_db:
            if to_date and transfer["transfer_date"] > to_date:
                continue
            if from_date and transfer["transfer_date"] < from_date:
                continue

            if (
                transfer["from_bank"] == bank
                and transfer["from_account"] == account_number
            ) or (
                transfer["to_bank"] == bank and transfer["to_account"] == account_number
            ):
                transfers.append(Transfer(**transfer))
        return transfers

    @staticmethod
    def get_balance(bank: str, account_number: str) -> int:
        balance = 0
        transfers = TransferRepository.list(bank=bank, account_number=account_number)
        for transfer in transfers:
            if transfer.from_account == account_number:
                balance -= transfer.amount
            else:
                balance += transfer.amount
        return balance

    @staticmethod
    def create(
        from_bank: str,
        from_account: str,
        to_bank: str,
        to_account: str,
        amount: int,
        transfer_date: datetime,
    ) -> bool:
        balance = TransferRepository.get_balance(
            bank=from_bank, account_number=from_account
        )
        if balance < amount:
            raise LowBalanceException(f"Balance too low for transfer, max={balance}")
        fake_transfer_db.append(
            {
                "from_bank": from_bank,
                "from_account": from_account,
                "to_bank": to_bank,
                "to_account": to_account,
                "amount": amount,
                "transfer_date": transfer_date,
            }
        )
