from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.exceptions.low_balance_exception import LowBalanceException
from app.models.user_model import User, UserInDB
from app.models.account_model import Account
from app.models.transfer_model import Transfer, NewTransfer
from app.repositories.user_repository import fake_users_db
from app.services.account_service import AccountService
from app.services.transfer_service import TransferService

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

app = FastAPI()


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return current_user


@app.post("/login")
def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@app.get("/users/me/")
def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user


@app.get("/users/me/accounts")
def get_my_accounts(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> list[Account]:
    return AccountService.list(username=current_user.username)


@app.get("/accounts/{bank}/{account_number}")
def get_account_details(
    bank,
    account_number,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> Account:
    if AccountService.does_user_own_account(
        username=current_user.username, bank=bank, account_number=account_number
    ):
        balance = TransferService.get_balance(bank=bank, account_number=account_number)
        return Account(
            user=current_user.username,
            bank=bank,
            account_number=account_number,
            balance=balance,
        )
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Account not found",
    )


@app.get("/accounts/{bank}/{account_number}/transfers")
def get_account_transfers(
    bank,
    account_number,
    current_user: Annotated[User, Depends(get_current_active_user)],
    from_date: datetime = None,
    to_date: datetime = None,
) -> list[Transfer]:
    if AccountService.does_user_own_account(
        username=current_user.username, bank=bank, account_number=account_number
    ):
        return TransferService.list(
            bank=bank,
            account_number=account_number,
            from_date=from_date,
            to_date=to_date,
        )
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Account not found",
    )


@app.post(
    "/accounts/{bank}/{account_number}/transfers", status_code=status.HTTP_201_CREATED
)
def create_account_transfer(
    transfer: NewTransfer,
    bank: str,
    account_number: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    try:
        if AccountService.does_user_own_account(
            username=current_user.username, bank=bank, account_number=account_number
        ):
            return TransferService.create(
                to_bank=transfer.to_bank,
                to_account=transfer.to_account,
                amount=transfer.amount,
                from_bank=bank,
                from_account=account_number,
            )
    except LowBalanceException as exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Balance to low",
        ) from exception
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Account not found",
    )
