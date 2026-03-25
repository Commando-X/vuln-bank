import pytest

from verifiers.sqli import (
    _check_sqli_login,
    _check_sqli_transfer,
    _check_sqli_graphql,
    _check_sqli_bills,
)


@pytest.mark.asyncio
async def test_sqli_login_positive(mock_ctx, make_request):
    ctx = mock_ctx(request_log=[
        make_request(
            method="POST",
            path="/login",
            body=b"username=admin' OR '1'='1'--&password=x",
            response_status=200,
        ),
    ])
    assert await _check_sqli_login(ctx) is True


@pytest.mark.asyncio
async def test_sqli_login_no_sqli(mock_ctx, make_request):
    ctx = mock_ctx(request_log=[
        make_request(
            method="POST",
            path="/login",
            body=b"username=admin&password=password123",
            response_status=200,
        ),
    ])
    assert await _check_sqli_login(ctx) is False


@pytest.mark.asyncio
async def test_sqli_login_sqli_but_failed(mock_ctx, make_request):
    ctx = mock_ctx(request_log=[
        make_request(
            method="POST",
            path="/login",
            body=b"username=admin' OR '1'='1'--&password=x",
            response_status=401,
        ),
    ])
    assert await _check_sqli_login(ctx) is False


@pytest.mark.asyncio
async def test_sqli_transfer_positive(mock_ctx, make_request):
    ctx = mock_ctx(request_log=[
        make_request(
            method="POST",
            path="/transfer",
            body=b"amount=100; DROP TABLE users--",
            response_status=200,
        ),
    ])
    assert await _check_sqli_transfer(ctx) is True


@pytest.mark.asyncio
async def test_sqli_transfer_negative(mock_ctx, make_request):
    ctx = mock_ctx(request_log=[
        make_request(
            method="POST",
            path="/transfer",
            body=b"amount=100&to=12345",
            response_status=200,
        ),
    ])
    assert await _check_sqli_transfer(ctx) is False


@pytest.mark.asyncio
async def test_sqli_graphql_positive(mock_ctx, make_request):
    ctx = mock_ctx(request_log=[
        make_request(
            method="POST",
            path="/graphql",
            body=b'{"query":"{ user(id: \\"1 UNION SELECT * FROM users--\\") { name } }"}',
            response_status=200,
        ),
    ])
    assert await _check_sqli_graphql(ctx) is True


@pytest.mark.asyncio
async def test_sqli_graphql_negative(mock_ctx, make_request):
    ctx = mock_ctx(request_log=[
        make_request(
            method="POST",
            path="/graphql",
            body=b'{"query":"{ user(id: 1) { name } }"}',
            response_status=200,
        ),
    ])
    assert await _check_sqli_graphql(ctx) is False


@pytest.mark.asyncio
async def test_sqli_bills_positive(mock_ctx, make_request):
    ctx = mock_ctx(request_log=[
        make_request(
            method="GET",
            path="/api/billers/by-category/' UNION SELECT * FROM users--",
            body=b"",
            response_status=200,
        ),
    ])
    assert await _check_sqli_bills(ctx) is True


@pytest.mark.asyncio
async def test_sqli_bills_negative(mock_ctx, make_request):
    ctx = mock_ctx(request_log=[
        make_request(
            method="GET",
            path="/api/billers/by-category/utilities",
            body=b"",
            response_status=200,
        ),
    ])
    assert await _check_sqli_bills(ctx) is False


@pytest.mark.asyncio
async def test_sqli_empty_log(mock_ctx):
    ctx = mock_ctx(request_log=[])
    assert await _check_sqli_login(ctx) is False
    assert await _check_sqli_transfer(ctx) is False
    assert await _check_sqli_graphql(ctx) is False
    assert await _check_sqli_bills(ctx) is False
