import pytest

from verifiers.ssrf import _check_ssrf_profile_url, _check_ssrf_metadata


@pytest.mark.asyncio
async def test_ssrf_profile_url_localhost(mock_ctx, make_request):
    ctx = mock_ctx(request_log=[
        make_request(
            method="POST",
            path="/upload_profile_picture_url",
            body=b"url=http://localhost:8080/admin",
            response_status=200,
        ),
    ])
    assert await _check_ssrf_profile_url(ctx) is True


@pytest.mark.asyncio
async def test_ssrf_profile_url_internal_ip(mock_ctx, make_request):
    ctx = mock_ctx(request_log=[
        make_request(
            method="POST",
            path="/upload_profile_picture_url",
            body=b"url=http://192.168.1.1/secret",
            response_status=200,
        ),
    ])
    assert await _check_ssrf_profile_url(ctx) is True


@pytest.mark.asyncio
async def test_ssrf_profile_url_127(mock_ctx, make_request):
    ctx = mock_ctx(request_log=[
        make_request(
            method="POST",
            path="/upload_profile_picture_url",
            body=b"url=http://127.0.0.1:3000/api",
            response_status=200,
        ),
    ])
    assert await _check_ssrf_profile_url(ctx) is True


@pytest.mark.asyncio
async def test_ssrf_profile_url_external(mock_ctx, make_request):
    ctx = mock_ctx(request_log=[
        make_request(
            method="POST",
            path="/upload_profile_picture_url",
            body=b"url=https://example.com/image.png",
            response_status=200,
        ),
    ])
    assert await _check_ssrf_profile_url(ctx) is False


@pytest.mark.asyncio
async def test_ssrf_profile_url_wrong_path(mock_ctx, make_request):
    ctx = mock_ctx(request_log=[
        make_request(
            method="POST",
            path="/upload_avatar",
            body=b"url=http://localhost:8080/admin",
            response_status=200,
        ),
    ])
    assert await _check_ssrf_profile_url(ctx) is False


@pytest.mark.asyncio
async def test_ssrf_metadata_aws(mock_ctx, make_request):
    ctx = mock_ctx(request_log=[
        make_request(
            method="POST",
            path="/upload_profile_picture_url",
            body=b"url=http://169.254.169.254/latest/meta-data/",
            response_status=200,
        ),
    ])
    assert await _check_ssrf_metadata(ctx) is True


@pytest.mark.asyncio
async def test_ssrf_metadata_gcp(mock_ctx, make_request):
    ctx = mock_ctx(request_log=[
        make_request(
            method="POST",
            path="/upload_profile_picture_url",
            body=b"url=http://metadata.google.internal/computeMetadata/v1/",
            response_status=200,
        ),
    ])
    assert await _check_ssrf_metadata(ctx) is True


@pytest.mark.asyncio
async def test_ssrf_metadata_no_metadata_url(mock_ctx, make_request):
    ctx = mock_ctx(request_log=[
        make_request(
            method="POST",
            path="/upload_profile_picture_url",
            body=b"url=http://localhost:8080/admin",
            response_status=200,
        ),
    ])
    assert await _check_ssrf_metadata(ctx) is False


@pytest.mark.asyncio
async def test_ssrf_metadata_failed_status(mock_ctx, make_request):
    ctx = mock_ctx(request_log=[
        make_request(
            method="POST",
            path="/upload_profile_picture_url",
            body=b"url=http://169.254.169.254/latest/meta-data/",
            response_status=403,
        ),
    ])
    assert await _check_ssrf_metadata(ctx) is False


@pytest.mark.asyncio
async def test_ssrf_empty_log(mock_ctx):
    ctx = mock_ctx(request_log=[])
    assert await _check_ssrf_profile_url(ctx) is False
    assert await _check_ssrf_metadata(ctx) is False
