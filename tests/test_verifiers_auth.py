"""Tests for auth verifiers."""

import base64
import json

import jwt as pyjwt
import pytest

from verifiers.auth import (
    _check_auth_jwt_none,
    _check_auth_jwt_weak_secret,
    _check_auth_mass_assignment,
    _check_auth_weak_reset,
)


def _make_jwt_none(payload: dict) -> str:
    """Create a JWT with alg:none."""
    header = base64.urlsafe_b64encode(json.dumps({"alg": "none", "typ": "JWT"}).encode()).rstrip(b"=").decode()
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    return f"{header}.{body}."


def _make_jwt_hs256(payload: dict, secret: str) -> str:
    """Create a JWT with HS256."""
    return pyjwt.encode(payload, secret, algorithm="HS256")


# --- JWT None ---

@pytest.mark.asyncio
async def test_jwt_none_detected(mock_ctx, make_request):
    token = _make_jwt_none({"sub": "admin"})
    ctx = mock_ctx(request_log=[
        make_request(
            method="GET", path="/dashboard",
            headers={"Authorization": f"Bearer {token}"},
            response_status=200,
        ),
    ])
    assert await _check_auth_jwt_none(ctx) == 1.0


@pytest.mark.asyncio
async def test_jwt_none_rejected_401(mock_ctx, make_request):
    token = _make_jwt_none({"sub": "admin"})
    ctx = mock_ctx(request_log=[
        make_request(
            method="GET", path="/dashboard",
            headers={"Authorization": f"Bearer {token}"},
            response_status=401,
        ),
    ])
    assert await _check_auth_jwt_none(ctx) == 0.0


@pytest.mark.asyncio
async def test_jwt_none_no_token(mock_ctx, make_request):
    ctx = mock_ctx(request_log=[
        make_request(method="GET", path="/dashboard", headers={}, response_status=200),
    ])
    assert await _check_auth_jwt_none(ctx) == 0.0


# --- JWT Weak Secret ---

@pytest.mark.asyncio
async def test_jwt_weak_secret_forged(mock_ctx, make_request):
    secret = "supersecret"
    login_token = _make_jwt_hs256({"sub": "user1"}, secret)
    forged_token = _make_jwt_hs256({"sub": "admin", "role": "admin"}, secret)
    config = {"auth": {"jwt_secret": secret}}

    ctx = mock_ctx(request_log=[
        make_request(
            method="POST", path="/api/login",
            body='{"username":"user1","password":"pass"}',
            response_status=200,
            response_body=json.dumps({"token": login_token}),
        ),
        make_request(
            method="GET", path="/admin/dashboard",
            headers={"Authorization": f"Bearer {forged_token}"},
            response_status=200,
        ),
    ])
    assert await _check_auth_jwt_weak_secret(ctx, config) == 1.0


@pytest.mark.asyncio
async def test_jwt_weak_secret_login_issued(mock_ctx, make_request):
    secret = "supersecret"
    login_token = _make_jwt_hs256({"sub": "user1"}, secret)
    config = {"auth": {"jwt_secret": secret}}

    ctx = mock_ctx(request_log=[
        make_request(
            method="POST", path="/api/login",
            body='{"username":"user1","password":"pass"}',
            response_status=200,
            response_body=json.dumps({"token": login_token}),
        ),
        make_request(
            method="GET", path="/dashboard",
            headers={"Authorization": f"Bearer {login_token}"},
            response_status=200,
        ),
    ])
    assert await _check_auth_jwt_weak_secret(ctx, config) == 0.0


@pytest.mark.asyncio
async def test_jwt_weak_secret_no_secret(mock_ctx, make_request):
    config = {"auth": {"jwt_secret": ""}}
    ctx = mock_ctx(request_log=[])
    assert await _check_auth_jwt_weak_secret(ctx, config) == 0.0


# --- Mass Assignment ---

@pytest.mark.asyncio
async def test_mass_assignment_detected(mock_ctx, make_request):
    ctx = mock_ctx(request_log=[
        make_request(
            method="POST", path="/register",
            body=json.dumps({"username": "evil", "password": "pass", "is_admin": True}),
            response_status=200,
        ),
    ])
    assert await _check_auth_mass_assignment(ctx) == 1.0


@pytest.mark.asyncio
async def test_mass_assignment_role_field(mock_ctx, make_request):
    ctx = mock_ctx(request_log=[
        make_request(
            method="POST", path="/register",
            body=json.dumps({"username": "evil", "password": "pass", "role": "admin"}),
            response_status=200,
        ),
    ])
    assert await _check_auth_mass_assignment(ctx) == 1.0


@pytest.mark.asyncio
async def test_mass_assignment_normal(mock_ctx, make_request):
    ctx = mock_ctx(request_log=[
        make_request(
            method="POST", path="/register",
            body=json.dumps({"username": "user", "password": "pass"}),
            response_status=200,
        ),
    ])
    assert await _check_auth_mass_assignment(ctx) == 0.0


# --- Weak Reset ---

@pytest.mark.asyncio
async def test_weak_reset_brute_force(mock_ctx, make_request):
    reqs = [
        make_request(method="POST", path="/reset-password", body=f'{{"token":"{i}"}}', response_status=400)
        for i in range(9)
    ]
    reqs.append(make_request(method="POST", path="/reset-password", body='{"token":"correct"}', response_status=200))
    ctx = mock_ctx(request_log=reqs)
    assert await _check_auth_weak_reset(ctx) == 1.0


@pytest.mark.asyncio
async def test_weak_reset_not_enough_attempts(mock_ctx, make_request):
    reqs = [
        make_request(method="POST", path="/reset-password", body=f'{{"token":"{i}"}}', response_status=400)
        for i in range(5)
    ]
    reqs.append(make_request(method="POST", path="/reset-password", body='{"token":"ok"}', response_status=200))
    ctx = mock_ctx(request_log=reqs)
    assert await _check_auth_weak_reset(ctx) == 0.0


@pytest.mark.asyncio
async def test_weak_reset_many_but_no_success(mock_ctx, make_request):
    reqs = [
        make_request(method="POST", path="/api/v1/reset-password", body=f'{{"token":"{i}"}}', response_status=400)
        for i in range(15)
    ]
    ctx = mock_ctx(request_log=reqs)
    assert await _check_auth_weak_reset(ctx) == 0.0
