from verifiers.helpers import has_sqli_indicators


async def _check_sqli_login(ctx) -> bool:
    for req in ctx.get_request_log():
        if req.method == "POST" and req.path == "/login":
            body = req.body.decode("utf-8", errors="ignore")
            if has_sqli_indicators(body) and req.response_status == 200:
                return True
    return False


async def _check_sqli_transfer(ctx) -> bool:
    for req in ctx.get_request_log():
        if req.method == "POST" and req.path == "/transfer":
            body = req.body.decode("utf-8", errors="ignore")
            if has_sqli_indicators(body) and req.response_status == 200:
                return True
    return False


async def _check_sqli_graphql(ctx) -> bool:
    for req in ctx.get_request_log():
        if req.method == "POST" and req.path == "/graphql":
            body = req.body.decode("utf-8", errors="ignore")
            if has_sqli_indicators(body) and req.response_status == 200:
                return True
    return False


async def _check_sqli_bills(ctx) -> bool:
    for req in ctx.get_request_log():
        if req.path.startswith("/api/billers/by-category/"):
            if has_sqli_indicators(req.path) and req.response_status == 200:
                return True
    return False


def register_sqli_login(wrapper, config):
    @wrapper.objective(name="sqli-login", description="Bypass authentication via SQL injection on /login", public=False)
    async def check(ctx):
        return await _check_sqli_login(ctx)


def register_sqli_transfer(wrapper, config):
    @wrapper.objective(name="sqli-transfer", description="Exploit SQL injection in transfer endpoint", public=False)
    async def check(ctx):
        return await _check_sqli_transfer(ctx)


def register_sqli_graphql(wrapper, config):
    @wrapper.objective(name="sqli-graphql", description="Exploit SQL injection in GraphQL resolvers", public=False)
    async def check(ctx):
        return await _check_sqli_graphql(ctx)


def register_sqli_bills(wrapper, config):
    @wrapper.objective(name="sqli-bills", description="Exploit SQL injection in biller queries", public=False)
    async def check(ctx):
        return await _check_sqli_bills(ctx)
