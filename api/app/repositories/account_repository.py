from app.models.account_model import Account

fake_accounts_db = [
    {"user": "johndoe", "bank": "33-01-02", "account_number": "123456"},
    {"user": "johndoe", "bank": "33-01-02", "account_number": "123457"},
    {"user": "mroubaud", "bank": "33-01-02", "account_number": "789098"},
]


class AccountRepository:
    @staticmethod
    def list(username: str) -> list[Account]:
        accounts = []
        for account in fake_accounts_db:
            if account["user"] == username:
                accounts.append(Account(**account))
        return accounts
