"""Tests for page coverage verifier."""

import pytest

from verifiers.coverage import _check_page_coverage, KNOWN_PATHS


@pytest.mark.asyncio
async def test_coverage_full(mock_ctx, make_request):
    reqs = [make_request(method="GET", path=p) for p in KNOWN_PATHS]
    ctx = mock_ctx(request_log=reqs)
    assert await _check_page_coverage(ctx) == 1.0


@pytest.mark.asyncio
async def test_coverage_partial(mock_ctx, make_request):
    paths = ["/", "/dashboard", "/login"]
    ctx = mock_ctx(request_log=[make_request(method="GET", path=p) for p in paths])
    score = await _check_page_coverage(ctx)
    assert score == pytest.approx(3 / len(KNOWN_PATHS))


@pytest.mark.asyncio
async def test_coverage_with_params(mock_ctx, make_request):
    """Numeric path segments should be normalized to {param}."""
    ctx = mock_ctx(request_log=[
        make_request(method="GET", path="/transactions/12345"),
        make_request(method="GET", path="/check_balance/99"),
    ])
    score = await _check_page_coverage(ctx)
    assert score == pytest.approx(2 / len(KNOWN_PATHS))


@pytest.mark.asyncio
async def test_coverage_empty(mock_ctx):
    ctx = mock_ctx(request_log=[])
    assert await _check_page_coverage(ctx) == 0.0


@pytest.mark.asyncio
async def test_coverage_unknown_paths(mock_ctx, make_request):
    ctx = mock_ctx(request_log=[
        make_request(method="GET", path="/nonexistent"),
        make_request(method="GET", path="/foo/bar"),
    ])
    assert await _check_page_coverage(ctx) == 0.0


@pytest.mark.asyncio
async def test_coverage_dedup(mock_ctx, make_request):
    """Visiting the same path multiple times should not inflate the score."""
    ctx = mock_ctx(request_log=[
        make_request(method="GET", path="/"),
        make_request(method="GET", path="/"),
        make_request(method="GET", path="/"),
    ])
    score = await _check_page_coverage(ctx)
    assert score == pytest.approx(1 / len(KNOWN_PATHS))
