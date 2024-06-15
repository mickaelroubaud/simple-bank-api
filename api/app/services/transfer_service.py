from datetime import datetime

from app.models.transfer_model import Transfer
from app.repositories.transfer_repository import TransferRepository


class TransferService:
    @staticmethod
    def list(
        bank: str,
        account_number: str,
        from_date: datetime = None,
        to_date: datetime = None,
    ) -> list[Transfer]:
        return TransferRepository.list(
            bank=bank,
            account_number=account_number,
            from_date=from_date,
            to_date=to_date,
        )

    @staticmethod
    def get_balance(bank: str, account_number: str) -> int:
        return TransferRepository.get_balance(bank=bank, account_number=account_number)

    @staticmethod
    def create(
        from_bank: str, from_account: str, to_bank: str, to_account: str, amount: int
    ) -> bool:

        return TransferRepository.create(
            from_bank=from_bank,
            from_account=from_account,
            to_bank=to_bank,
            to_account=to_account,
            amount=amount,
            transfer_date=datetime.now(),
        )
