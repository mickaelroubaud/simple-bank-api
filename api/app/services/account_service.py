from app.models.account_model import Account
from app.repositories.account_repository import AccountRepository
from app.services.transfer_service import TransferService


class AccountService:

    @staticmethod
    def does_user_own_account(username: str, bank: str, account_number: str) -> bool:
        user_accounts = AccountRepository.list(username)
        for account in user_accounts:
            if account.bank == bank and account.account_number == account_number:
                return True
        return False

    @staticmethod
    def list(username: str) -> list[Account]:
        accounts = AccountRepository.list(username=username)
        for account in accounts:
            account.balance = TransferService.get_balance(
                bank=account.bank, account_number=account.account_number
            )
        return accounts

    @staticmethod
    def get(
        username: str,
        bank: str,
        account_number: str,
    ) -> Account:
        balance = TransferService.get_balance(bank=bank, account_number=account_number)
        return Account(
            user=username,
            bank=bank,
            account_number=account_number,
            balance=balance,
        )
