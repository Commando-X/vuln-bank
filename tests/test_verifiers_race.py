"""Tests for race condition verifier."""

import pytest

from verifiers.race_condition import _check_race_condition_transfer


@pytest.mark.asyncio
async def test_race_condition_detected(mock_ctx, make_request):
    body = '{"to": "user2", "amount": 100}'
    reqs = [
        make_request(method="POST", path="/api/transfer", body=body)
        for _ in range(5)
    ]
    ctx = mock_ctx(request_log=reqs)
    assert await _check_race_condition_transfer(ctx) == 1.0


@pytest.mark.asyncio
async def test_race_condition_exactly_three(mock_ctx, make_request):
    body = '{"to": "user2", "amount": 50}'
    reqs = [
        make_request(method="POST", path="/transfer", body=body)
        for _ in range(3)
    ]
    ctx = mock_ctx(request_log=reqs)
    assert await _check_race_condition_transfer(ctx) == 1.0


@pytest.mark.asyncio
async def test_race_condition_below_threshold(mock_ctx, make_request):
    body = '{"to": "user2", "amount": 100}'
    reqs = [
        make_request(method="POST", path="/api/transfer", body=body)
        for _ in range(2)
    ]
    ctx = mock_ctx(request_log=reqs)
    assert await _check_race_condition_transfer(ctx) == 0.0


@pytest.mark.asyncio
async def test_race_condition_different_bodies(mock_ctx, make_request):
    reqs = [
        make_request(method="POST", path="/api/transfer", body=f'{{"to": "user{i}", "amount": 100}}')
        for i in range(5)
    ]
    ctx = mock_ctx(request_log=reqs)
    assert await _check_race_condition_transfer(ctx) == 0.0


@pytest.mark.asyncio
async def test_race_condition_empty(mock_ctx):
    ctx = mock_ctx(request_log=[])
    assert await _check_race_condition_transfer(ctx) == 0.0


@pytest.mark.asyncio
async def test_race_condition_wrong_method(mock_ctx, make_request):
    body = '{"to": "user2", "amount": 100}'
    reqs = [
        make_request(method="GET", path="/api/transfer", body=body)
        for _ in range(5)
    ]
    ctx = mock_ctx(request_log=reqs)
    assert await _check_race_condition_transfer(ctx) == 0.0
