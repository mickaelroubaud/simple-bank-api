from fastapi.testclient import TestClient
import pytest

from .main import app

client = TestClient(app)
fake_login_data = {"username": "johndoe", "password": "secret"}


@pytest.fixture(name="get_auth_headers")
def login():
    access_token = client.post("/login", data=fake_login_data).json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


def test_login():
    response = client.post("/login", data=fake_login_data)
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"


def test_get_user(get_auth_headers):
    response = client.get("/users/me", headers=get_auth_headers)
    assert response.status_code == 200
    assert response.json()["full_name"] == "John Doe"


def test_get_user_accounts(get_auth_headers):
    response = client.get("/users/me/accounts", headers=get_auth_headers)
    assert response.status_code == 200
    accounts = response.json()
    assert len(accounts) == 2
    assert accounts[0]["account_number"] == "123456"
    assert accounts[1]["account_number"] == "123457"


def test_get_default_balance(get_auth_headers):
    response = client.get("/accounts/33-01-02/123456", headers=get_auth_headers)
    assert response.status_code == 200
    assert response.json()["balance"] == 67


def test_cannot_access_other_account(get_auth_headers):
    response = client.get("/accounts/33-01-02/789098", headers=get_auth_headers)
    assert response.status_code == 404


def test_add_transfers(get_auth_headers):
    response = client.get("/accounts/33-01-02/123456", headers=get_auth_headers)
    balance = response.json()["balance"]

    response = client.post(
        "/accounts/33-01-02/123456/transfers",
        json={"to_bank": "11-33-44", "to_account": "3333", "amount": 2},
        headers=get_auth_headers,
    )
    assert response.status_code == 201
    response = client.post(
        "/accounts/33-01-02/123456/transfers",
        json={"to_bank": "11-33-44", "to_account": "4444", "amount": 1},
        headers=get_auth_headers,
    )
    assert response.status_code == 201
    response = client.get("/accounts/33-01-02/123456", headers=get_auth_headers)
    assert balance - 3 == response.json()["balance"]


def test_low_balance(get_auth_headers):
    response = client.get("/accounts/33-01-02/123456", headers=get_auth_headers)
    balance = response.json()["balance"]

    response = client.post(
        "/accounts/33-01-02/123456/transfers",
        json={"to_bank": "11-33-44", "to_account": "3333", "amount": balance + 1},
        headers=get_auth_headers,
    )

    assert response.status_code == 400


def test_list_transfers(get_auth_headers):
    balance = client.get("/accounts/33-01-02/123457", headers=get_auth_headers).json()[
        "balance"
    ]
    response = client.post(
        "/accounts/33-01-02/123457/transfers",
        json={"to_bank": "11-33-44", "to_account": "3333", "amount": 1},
        headers=get_auth_headers,
    )
    response = client.post(
        "/accounts/33-01-02/123457/transfers",
        json={"to_bank": "11-33-44", "to_account": "4444", "amount": 2},
        headers=get_auth_headers,
    )
    # this transfer must be ignored
    response = client.post(
        "/accounts/33-01-02/123457/transfers",
        json={"to_bank": "11-33-44", "to_account": "5555", "amount": balance + 1},
        headers=get_auth_headers,
    )
    # this transfer is from another account
    response = client.post(
        "/accounts/33-01-02/123456/transfers",
        json={"to_bank": "11-33-44", "to_account": "5555", "amount": 1},
        headers=get_auth_headers,
    )
    response = client.get(
        "/accounts/33-01-02/123457/transfers", headers=get_auth_headers
    )
    assert response.status_code == 200
    assert '"to_account":"4444"' in response.text
    assert '"to_account":"3333"' in response.text
    assert '"to_account":"5555"' not in response.text


def test_list_transfers_filtered_by_date(get_auth_headers):
    response = client.get(
        "/accounts/33-01-02/123457/transfers?from_date=1988-01-01",
        headers=get_auth_headers,
    )
    assert len(response.json()) > 0
    response = client.get(
        "/accounts/33-01-02/123457/transfers?from_date=1988-01-01&to_date=1989-01-01",
        headers=get_auth_headers,
    )
    assert len(response.json()) == 0
    response = client.get(
        "/accounts/33-01-02/123457/transfers?to_date=1989-01-01",
        headers=get_auth_headers,
    )
    assert len(response.json()) == 0
    response = client.get(
        "/accounts/33-01-02/123457/transfers?to_date=2100-01-01",
        headers=get_auth_headers,
    )
    assert len(response.json()) > 0


def test_transfer_from_account_to_another(get_auth_headers):
    response = client.get("/accounts/33-01-02/123456", headers=get_auth_headers)
    balance1 = response.json()["balance"]
    response = client.get("/accounts/33-01-02/123457", headers=get_auth_headers)
    balance2 = response.json()["balance"]

    client.post(
        "/accounts/33-01-02/123456/transfers",
        json={"to_bank": "33-01-02", "to_account": "123457", "amount": 1},
        headers=get_auth_headers,
    )
    assert (
        client.get("/accounts/33-01-02/123456", headers=get_auth_headers).json()[
            "balance"
        ]
        == balance1 - 1
    )
    assert (
        client.get("/accounts/33-01-02/123457", headers=get_auth_headers).json()[
            "balance"
        ]
        == balance2 + 1
    )
