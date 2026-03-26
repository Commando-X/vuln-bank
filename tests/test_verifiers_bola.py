import json

import jwt
import pytest

from verifiers.bola import (
    _check_bola_transactions,
    _check_bola_balance,
    _check_bola_cards,
    _check_bola_bills,
)

SECRET = "secret123"
CONFIG = {"auth": {"jwt_secret": SECRET}}


def _make_token(user_id, username="testuser", is_admin=False):
    return jwt.encode(
        {"user_id": user_id, "username": username, "is_admin": is_admin},
        SECRET,
        algorithm="HS256",
    )


@pytest.mark.asyncio
async def test_bola_transactions_positive(mock_ctx, make_request):
    token = _make_token(user_id=1)
    ctx = mock_ctx(request_log=[
        make_request(
            method="GET",
            path="/transactions/999999",
            headers={"authorization": f"Bearer {token}"},
            body=b"",
            response_status=200,
        ),
    ])
    # User 1 has account 111111 but is accessing account 999999
    exec_key = "sqlite3 /app/data/vulnbank.db SELECT account_number FROM users WHERE id = 1"
    ctx._exec_results[exec_key] = "  111111\n"
    assert await _check_bola_transactions(ctx, CONFIG) is True


@pytest.mark.asyncio
async def test_bola_transactions_own_account(mock_ctx, make_request):
    token = _make_token(user_id=1)
    ctx = mock_ctx(request_log=[
        make_request(
            method="GET",
            path="/transactions/111111",
            headers={"authorization": f"Bearer {token}"},
            body=b"",
            response_status=200,
        ),
    ])
    exec_key = "sqlite3 /app/data/vulnbank.db SELECT account_number FROM users WHERE id = 1"
    ctx._exec_results[exec_key] = "  111111\n"
    assert await _check_bola_transactions(ctx, CONFIG) is False


@pytest.mark.asyncio
async def test_bola_transactions_no_auth(mock_ctx, make_request):
    ctx = mock_ctx(request_log=[
        make_request(
            method="GET",
            path="/transactions/999999",
            headers={},
            body=b"",
            response_status=200,
        ),
    ])
    assert await _check_bola_transactions(ctx, CONFIG) is False


@pytest.mark.asyncio
async def test_bola_balance_positive(mock_ctx, make_request):
    token = _make_token(user_id=2)
    ctx = mock_ctx(request_log=[
        make_request(
            method="GET",
            path="/check_balance/888888",
            headers={"authorization": f"Bearer {token}"},
            body=b"",
            response_status=200,
        ),
    ])
    exec_key = "sqlite3 /app/data/vulnbank.db SELECT account_number FROM users WHERE id = 2"
    ctx._exec_results[exec_key] = "  222222\n"
    assert await _check_bola_balance(ctx, CONFIG) is True


@pytest.mark.asyncio
async def test_bola_balance_own_account(mock_ctx, make_request):
    token = _make_token(user_id=2)
    ctx = mock_ctx(request_log=[
        make_request(
            method="GET",
            path="/check_balance/222222",
            headers={"authorization": f"Bearer {token}"},
            body=b"",
            response_status=200,
        ),
    ])
    exec_key = "sqlite3 /app/data/vulnbank.db SELECT account_number FROM users WHERE id = 2"
    ctx._exec_results[exec_key] = "  222222\n"
    assert await _check_bola_balance(ctx, CONFIG) is False


@pytest.mark.asyncio
async def test_bola_cards_positive(mock_ctx, make_request):
    token = _make_token(user_id=1)
    resp_body = json.dumps([{"user_id": 2, "card_number": "4111111111111111", "cvv": "123"}])
    ctx = mock_ctx(request_log=[
        make_request(
            method="GET",
            path="/api/cards",
            headers={"authorization": f"Bearer {token}"},
            body=b"",
            response_status=200,
            response_body=resp_body,
        ),
    ])
    assert await _check_bola_cards(ctx, CONFIG) is True


@pytest.mark.asyncio
async def test_bola_cards_own_data(mock_ctx, make_request):
    token = _make_token(user_id=1)
    resp_body = json.dumps([{"user_id": 1, "card_number": "4111111111111111", "cvv": "123"}])
    ctx = mock_ctx(request_log=[
        make_request(
            method="GET",
            path="/api/cards",
            headers={"authorization": f"Bearer {token}"},
            body=b"",
            response_status=200,
            response_body=resp_body,
        ),
    ])
    assert await _check_bola_cards(ctx, CONFIG) is False


@pytest.mark.asyncio
async def test_bola_cards_no_sensitive_fields(mock_ctx, make_request):
    token = _make_token(user_id=1)
    resp_body = json.dumps([{"user_id": 2, "card_type": "visa"}])
    ctx = mock_ctx(request_log=[
        make_request(
            method="GET",
            path="/api/cards",
            headers={"authorization": f"Bearer {token}"},
            body=b"",
            response_status=200,
            response_body=resp_body,
        ),
    ])
    assert await _check_bola_cards(ctx, CONFIG) is False


@pytest.mark.asyncio
async def test_bola_bills_positive(mock_ctx, make_request):
    token = _make_token(user_id=1)
    resp_body = json.dumps([{"user_id": 3, "amount": 50.0, "biller": "Electric Co"}])
    ctx = mock_ctx(request_log=[
        make_request(
            method="GET",
            path="/api/bills",
            headers={"authorization": f"Bearer {token}"},
            body=b"",
            response_status=200,
            response_body=resp_body,
        ),
    ])
    assert await _check_bola_bills(ctx, CONFIG) is True


@pytest.mark.asyncio
async def test_bola_bills_own_data(mock_ctx, make_request):
    token = _make_token(user_id=1)
    resp_body = json.dumps([{"user_id": 1, "amount": 50.0, "biller": "Electric Co"}])
    ctx = mock_ctx(request_log=[
        make_request(
            method="GET",
            path="/api/bills",
            headers={"authorization": f"Bearer {token}"},
            body=b"",
            response_status=200,
            response_body=resp_body,
        ),
    ])
    assert await _check_bola_bills(ctx, CONFIG) is False


@pytest.mark.asyncio
async def test_bola_bills_no_auth(mock_ctx, make_request):
    resp_body = json.dumps([{"user_id": 3, "amount": 50.0}])
    ctx = mock_ctx(request_log=[
        make_request(
            method="GET",
            path="/api/bills",
            headers={},
            body=b"",
            response_status=200,
            response_body=resp_body,
        ),
    ])
    assert await _check_bola_bills(ctx, CONFIG) is False


@pytest.mark.asyncio
async def test_bola_empty_log(mock_ctx):
    ctx = mock_ctx(request_log=[])
    assert await _check_bola_transactions(ctx, CONFIG) is False
    assert await _check_bola_balance(ctx, CONFIG) is False
    assert await _check_bola_cards(ctx, CONFIG) is False
    assert await _check_bola_bills(ctx, CONFIG) is False
