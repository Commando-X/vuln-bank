import re

_INTERNAL_URL_PATTERNS = re.compile(
    r"(localhost|127\.0\.0\.1|0\.0\.0\.0|::1|internal|10\.\d+\.\d+\.\d+|172\.(1[6-9]|2\d|3[01])\.\d+\.\d+|192\.168\.\d+\.\d+)",
    re.IGNORECASE,
)

_METADATA_URL_PATTERNS = re.compile(
    r"(169\.254\.169\.254|metadata\.google|100\.100\.100\.200)",
    re.IGNORECASE,
)


async def _check_ssrf_profile_url(ctx) -> bool:
    for req in ctx.get_request_log():
        if req.method == "POST" and req.path == "/upload_profile_picture_url":
            body = req.body.decode("utf-8", errors="ignore")
            if _INTERNAL_URL_PATTERNS.search(body) and req.response_status == 200:
                return True
    return False


async def _check_ssrf_metadata(ctx) -> bool:
    for req in ctx.get_request_log():
        if req.method == "POST" and req.path == "/upload_profile_picture_url":
            body = req.body.decode("utf-8", errors="ignore")
            if _METADATA_URL_PATTERNS.search(body) and req.response_status == 200:
                return True
    return False


def register_ssrf_profile_url(wrapper, config):
    @wrapper.objective(name="ssrf-profile-url", description="Exploit SSRF via profile picture URL to access internal services", public=False)
    async def check(ctx):
        return await _check_ssrf_profile_url(ctx)


def register_ssrf_metadata(wrapper, config):
    @wrapper.objective(name="ssrf-metadata", description="Exploit SSRF to access cloud metadata endpoints", public=False)
    async def check(ctx):
        return await _check_ssrf_metadata(ctx)
