import pytest

from verifiers.xss import _check_xss_bio_stored


@pytest.mark.asyncio
async def test_xss_bio_stored_script_tag(mock_ctx, make_request):
    ctx = mock_ctx(request_log=[
        make_request(
            method="POST",
            path="/update_bio",
            body=b'bio=<script>alert("xss")</script>',
            response_status=200,
        ),
    ])
    assert await _check_xss_bio_stored(ctx) is True


@pytest.mark.asyncio
async def test_xss_bio_stored_event_handler(mock_ctx, make_request):
    ctx = mock_ctx(request_log=[
        make_request(
            method="POST",
            path="/update_bio",
            body=b'bio=<img onerror=alert(1) src=x>',
            response_status=200,
        ),
    ])
    assert await _check_xss_bio_stored(ctx) is True


@pytest.mark.asyncio
async def test_xss_bio_stored_javascript_uri(mock_ctx, make_request):
    ctx = mock_ctx(request_log=[
        make_request(
            method="POST",
            path="/update_bio",
            body=b'bio=<a href="javascript:alert(1)">click</a>',
            response_status=200,
        ),
    ])
    assert await _check_xss_bio_stored(ctx) is True


@pytest.mark.asyncio
async def test_xss_bio_stored_no_xss(mock_ctx, make_request):
    ctx = mock_ctx(request_log=[
        make_request(
            method="POST",
            path="/update_bio",
            body=b"bio=Hello, I am a normal user.",
            response_status=200,
        ),
    ])
    assert await _check_xss_bio_stored(ctx) is False


@pytest.mark.asyncio
async def test_xss_bio_stored_wrong_path(mock_ctx, make_request):
    ctx = mock_ctx(request_log=[
        make_request(
            method="POST",
            path="/update_profile",
            body=b'bio=<script>alert(1)</script>',
            response_status=200,
        ),
    ])
    assert await _check_xss_bio_stored(ctx) is False


@pytest.mark.asyncio
async def test_xss_bio_stored_failed_status(mock_ctx, make_request):
    ctx = mock_ctx(request_log=[
        make_request(
            method="POST",
            path="/update_bio",
            body=b'bio=<script>alert(1)</script>',
            response_status=400,
        ),
    ])
    assert await _check_xss_bio_stored(ctx) is False


@pytest.mark.asyncio
async def test_xss_bio_stored_empty_log(mock_ctx):
    ctx = mock_ctx(request_log=[])
    assert await _check_xss_bio_stored(ctx) is False
