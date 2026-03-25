"""Tests for file upload verifiers."""

import pytest

from verifiers.file_upload import (
    _check_file_upload_path_traversal,
    _check_file_upload_unrestricted,
)


@pytest.mark.asyncio
async def test_path_traversal_detected(mock_ctx, make_request):
    body = (
        '------boundary\r\n'
        'Content-Disposition: form-data; name="file"; filename="../../../etc/passwd"\r\n'
        'Content-Type: application/octet-stream\r\n\r\n'
        'file content\r\n'
        '------boundary--'
    )
    ctx = mock_ctx(request_log=[
        make_request(method="POST", path="/upload_profile_picture", body=body),
    ])
    assert await _check_file_upload_path_traversal(ctx) == 1.0


@pytest.mark.asyncio
async def test_path_traversal_safe_filename(mock_ctx, make_request):
    body = (
        '------boundary\r\n'
        'Content-Disposition: form-data; name="file"; filename="photo.jpg"\r\n'
        'Content-Type: image/jpeg\r\n\r\n'
        'data\r\n'
        '------boundary--'
    )
    ctx = mock_ctx(request_log=[
        make_request(method="POST", path="/upload_profile_picture", body=body),
    ])
    assert await _check_file_upload_path_traversal(ctx) == 0.0


@pytest.mark.asyncio
async def test_path_traversal_no_upload(mock_ctx):
    ctx = mock_ctx(request_log=[])
    assert await _check_file_upload_path_traversal(ctx) == 0.0


@pytest.mark.asyncio
async def test_unrestricted_php(mock_ctx, make_request):
    body = (
        '------boundary\r\n'
        'Content-Disposition: form-data; name="file"; filename="shell.php"\r\n'
        'Content-Type: application/x-php\r\n\r\n'
        '<?php system($_GET["cmd"]); ?>\r\n'
        '------boundary--'
    )
    ctx = mock_ctx(request_log=[
        make_request(method="POST", path="/upload_profile_picture", body=body),
    ])
    assert await _check_file_upload_unrestricted(ctx) == 1.0


@pytest.mark.asyncio
async def test_unrestricted_svg(mock_ctx, make_request):
    body = (
        '------boundary\r\n'
        'Content-Disposition: form-data; name="file"; filename="evil.svg"\r\n'
        'Content-Type: image/svg+xml\r\n\r\n'
        '<svg onload="alert(1)"></svg>\r\n'
        '------boundary--'
    )
    ctx = mock_ctx(request_log=[
        make_request(method="POST", path="/upload_profile_picture", body=body),
    ])
    assert await _check_file_upload_unrestricted(ctx) == 1.0


@pytest.mark.asyncio
async def test_unrestricted_safe_jpg(mock_ctx, make_request):
    body = (
        '------boundary\r\n'
        'Content-Disposition: form-data; name="file"; filename="photo.jpg"\r\n'
        'Content-Type: image/jpeg\r\n\r\n'
        'data\r\n'
        '------boundary--'
    )
    ctx = mock_ctx(request_log=[
        make_request(method="POST", path="/upload_profile_picture", body=body),
    ])
    assert await _check_file_upload_unrestricted(ctx) == 0.0


@pytest.mark.asyncio
async def test_unrestricted_get_ignored(mock_ctx, make_request):
    body = 'Content-Disposition: form-data; name="file"; filename="shell.php"'
    ctx = mock_ctx(request_log=[
        make_request(method="GET", path="/upload_profile_picture", body=body),
    ])
    assert await _check_file_upload_unrestricted(ctx) == 0.0
