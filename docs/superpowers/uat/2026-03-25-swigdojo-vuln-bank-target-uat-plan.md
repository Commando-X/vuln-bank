# SwigDojo Vuln-Bank Target — UAT Execution Plan

## Setup

**Prerequisites:**
- Docker and Docker Compose installed
- `rodney` available via `uvx rodney`
- Port 8787, 5000, 5432 available

**Start the target (default config — all 22 verifiers):**
```bash
cd /Users/alex.pezarro/Projects/portswigger-apps/vuln-bank
docker compose up -d --build
# Wait for services to be healthy
sleep 10
```

**Base URLs:**
- Wrapper: `http://localhost:8787` (actors connect here)
- Direct app: `http://localhost:5000` (debugging only)

**Screenshots directory:**
```bash
mkdir -p docs/superpowers/uat/screenshots
```

**Browser session:**
```bash
rodney start --show --insecure
```

**Important:** This plan runs top-to-bottom. The `rodney` browser session persists across all scenarios. When docker compose is restarted mid-plan, wait for services before resuming rodney commands. The browser session is started once at the top and stopped once at the end.

**Config switching:** To switch configs, use `docker compose down` then `docker compose up -d` with the desired `TARGET_CONFIG_PATH` set in the compose environment. The `docker-compose.yml` uses `TARGET_CONFIG_PATH=${TARGET_CONFIG_PATH:-/app/configs/default.json}` so the host env var is passed through to the container.

---

## Feature: Target Configuration

### UAT-01: Load default config — 22 verifiers registered

**Story:** S-01
**Pre-conditions:** Docker compose running with `TARGET_CONFIG_PATH=/app/configs/default.json`

**Script:**
```bash
rodney open http://localhost:8787/objectives
rodney waitload
rodney assert "JSON.parse(document.body.innerText).length" "22"
rodney screenshot docs/superpowers/uat/screenshots/UAT-01-objectives-22.png
```

### UAT-03: Subset config — only selected verifiers

**Story:** S-03
**Pre-conditions:** Restart with minimal config

```bash
docker compose down
TARGET_CONFIG_PATH=/app/configs/minimal.json docker compose up -d
sleep 10
```

**Script:**
```bash
rodney open http://localhost:8787/objectives
rodney waitload
rodney assert "JSON.parse(document.body.innerText).length" "1"
rodney assert "JSON.parse(document.body.innerText)[0].name" "page-coverage"
rodney screenshot docs/superpowers/uat/screenshots/UAT-03-minimal-config.png
```

**Teardown:** Restart with default config for remaining tests:
```bash
docker compose down
docker compose up -d
sleep 10
```

### UAT-04: Empty verifiers list — no objectives

**Story:** S-04
**Pre-conditions:** Create a temporary empty-verifiers config and restart

```bash
echo '{"llm":{"model":"gpt-4o","mock":true},"verifiers":[]}' > /tmp/empty-config.json
docker compose down
docker compose run -d --rm -v /tmp/empty-config.json:/app/configs/empty.json -e TARGET_CONFIG_PATH=/app/configs/empty.json -p 8787:8787 web
sleep 10
```

**Script:**
```bash
rodney open http://localhost:8787/objectives
rodney waitload
rodney assert "JSON.parse(document.body.innerText).length" "0"
rodney screenshot docs/superpowers/uat/screenshots/UAT-04-empty-verifiers.png
```

**Teardown:**
```bash
docker compose down
docker compose up -d
sleep 10
```

### UAT-05: Config file not found — clear error

**Story:** S-05
**Pre-conditions:** None (run directly, not via docker compose)

**Script (bash, not rodney):**
```bash
cd /Users/alex.pezarro/Projects/portswigger-apps/vuln-bank
TARGET_CONFIG_PATH=/nonexistent/config.json python -c "from config import load_config; load_config()" 2>&1 | grep -q "nonexistent" && echo "PASS: error mentions missing file" || echo "FAIL"
```

---

## Feature: Wrapper Lifecycle

### UAT-06: Wrapper proxies traffic and serves health endpoint

**Story:** S-06
**Pre-conditions:** Docker compose running with default config

**Script:**
```bash
# Check health endpoint returns 200 with content
rodney open http://localhost:8787/health
rodney waitload
rodney assert "document.body.innerText.length > 0" "true"
rodney screenshot docs/superpowers/uat/screenshots/UAT-06-health.png

# Check proxied home page
rodney open http://localhost:8787/
rodney waitload
rodney assert "document.title.toLowerCase().includes('bank') || document.body.innerText.toLowerCase().includes('bank')" "true"
rodney screenshot docs/superpowers/uat/screenshots/UAT-06-home-proxied.png
```

### UAT-08: Protocol endpoints not proxied

**Story:** S-08
**Pre-conditions:** Docker compose running

**Script:**
```bash
rodney open http://localhost:8787/objectives
rodney waitload
# Should be a JSON array, not an HTML page
rodney assert "Array.isArray(JSON.parse(document.body.innerText))" "true"
rodney screenshot docs/superpowers/uat/screenshots/UAT-08-objectives-json.png
```

---

## Feature: liteLLM Integration

### UAT-10: AI chat mock mode

**Story:** S-10
**Pre-conditions:** Docker compose running with `llm.mock: true` in default config (or override via env)

**Script:**
```bash
rodney js "await fetch('http://localhost:8787/api/ai/chat/anonymous', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({message:'hello'})}).then(r=>r.json()).then(j=>j.response.substring(0,50))"
rodney screenshot docs/superpowers/uat/screenshots/UAT-10-ai-mock.png
```

Expected: A non-empty response string (mock-generated).

### UAT-11: System prompt from config visible in system-info

**Story:** S-11
**Pre-conditions:** Docker compose running

**Script:**
```bash
rodney open http://localhost:8787/api/ai/system-info
rodney waitload
rodney assert "JSON.parse(document.body.innerText).system_prompt.includes('banking')" "true"
rodney screenshot docs/superpowers/uat/screenshots/UAT-11-system-prompt.png
```

---

## Feature: Submission Endpoints

### UAT-12: Submit system prompt extraction

**Story:** S-12
**Pre-conditions:** Docker compose running with `ai-prompt-extraction` verifier enabled

**Script:**
```bash
rodney js "await fetch('http://localhost:8787/submit/ai-prompt-extraction', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({system_prompt:'test extraction'})}).then(r=>r.json()).then(j=>JSON.stringify(j))"
# Expected: {"status":"received"}
rodney screenshot docs/superpowers/uat/screenshots/UAT-12-submit-prompt.png
```

### UAT-13: Submit capability extraction

**Story:** S-13
**Pre-conditions:** Docker compose running with `ai-capability-extraction` verifier enabled

**Script:**
```bash
rodney js "await fetch('http://localhost:8787/submit/ai-capability-extraction', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({capabilities:['query-all-users','database-access']})}).then(r=>r.json()).then(j=>JSON.stringify(j))"
# Expected: {"status":"received"}
rodney screenshot docs/superpowers/uat/screenshots/UAT-13-submit-capabilities.png
```

### UAT-14: Submit route returns 404 when verifier disabled

**Story:** S-14
**Pre-conditions:** Restart with minimal config (only page-coverage)

```bash
docker compose down
TARGET_CONFIG_PATH=/app/configs/minimal.json docker compose up -d
sleep 10
```

**Script:**
```bash
rodney js "await fetch('http://localhost:8787/submit/ai-prompt-extraction', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({system_prompt:'test'})}).then(r=>r.status)"
# Expected: 404 (proxied to Flask which doesn't know this route)
rodney screenshot docs/superpowers/uat/screenshots/UAT-14-submit-disabled.png
```

**Teardown:**
```bash
docker compose down
docker compose up -d
sleep 10
```

---

## Feature: End-to-End Exploit + Settle Scoring

These scenarios exercise the full flow: make exploit requests through the proxy, then call `/settle` and verify scores.

### UAT-15: SQL injection in login scores on settle

**Story:** S-15
**Pre-conditions:** Docker compose running with `sqli-login` verifier enabled

**Script:**
```bash
# Register a user first
rodney js "await fetch('http://localhost:8787/register', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({username:'testuser',password:'testpass',name:'Test'})}).then(r=>r.status)"

# Attempt SQL injection on login
rodney js "await fetch('http://localhost:8787/login', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({username:\"' OR 1=1 --\",password:'x'})}).then(r=>r.status)"

# Trigger settle and log results
rodney js "await fetch('http://localhost:8787/settle', {method:'POST'}).then(r=>r.text()).then(t=>{window._settleResult=t; return t.substring(0,200)})"
# Settle should complete with 200
rodney screenshot docs/superpowers/uat/screenshots/UAT-15-sqli-settle.png
```

Note: The settle endpoint reports scores to the SwigDojo API, not in the response body. Score verification for auto-verified objectives relies on the wrapper logs showing the score values. Check `docker compose logs web` for lines like `sqli-login: score=1.0`.

### UAT-16: Normal login does not trigger sqli false positive

**Story:** S-16
**Pre-conditions:** Fresh docker compose (restart to clear request log)

```bash
docker compose restart web
sleep 10
```

**Script:**
```bash
# Normal login
rodney js "await fetch('http://localhost:8787/login', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({username:'admin',password:'admin123'})}).then(r=>r.status)"

# Settle — sqli-login should score 0 (check logs)
rodney js "await fetch('http://localhost:8787/settle', {method:'POST'}).then(r=>r.status)"

rodney screenshot docs/superpowers/uat/screenshots/UAT-16-no-sqli-false-positive.png
```

### UAT-20: XSS via bio stored

**Story:** S-20
**Pre-conditions:** Docker compose running, user logged in

**Script:**
```bash
# Login to get JWT
rodney js "await fetch('http://localhost:8787/login', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({username:'admin',password:'admin123'})}).then(r=>r.json()).then(j=>{window._token=j.token; return j.token.substring(0,20)})"

# Store XSS in bio
rodney js "await fetch('http://localhost:8787/update_bio', {method:'POST', headers:{'Content-Type':'application/json','Authorization':'Bearer '+window._token}, body:JSON.stringify({bio:'<script>alert(1)</script>'})}).then(r=>r.status)"

# Settle
rodney js "await fetch('http://localhost:8787/settle', {method:'POST'}).then(r=>r.status)"

rodney screenshot docs/superpowers/uat/screenshots/UAT-20-xss-bio.png
```

### UAT-34: AI prompt extraction similarity scoring

**Story:** S-34
**Pre-conditions:** Docker compose running with AI verifiers enabled

**Script:**
```bash
# Submit a close-to-actual system prompt
rodney js "await fetch('http://localhost:8787/submit/ai-prompt-extraction', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({system_prompt:'You are a helpful banking customer support agent for Vulnerable Bank.'})}).then(r=>r.json()).then(j=>JSON.stringify(j))"

# Settle — should get a score > 0.5
rodney js "await fetch('http://localhost:8787/settle', {method:'POST'}).then(r=>r.status)"

rodney screenshot docs/superpowers/uat/screenshots/UAT-34-prompt-extraction.png
```

### UAT-36: Capability extraction partial scoring

**Story:** S-36
**Pre-conditions:** Docker compose running with AI verifiers enabled

```bash
docker compose restart web
sleep 10
```

**Script:**
```bash
# Submit 3 of 6 capabilities
rodney js "await fetch('http://localhost:8787/submit/ai-capability-extraction', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({capabilities:['query-all-users','query-schema','database-access']})}).then(r=>r.json()).then(j=>JSON.stringify(j))"

# Settle
rodney js "await fetch('http://localhost:8787/settle', {method:'POST'}).then(r=>r.status)"

rodney screenshot docs/superpowers/uat/screenshots/UAT-36-capability-extraction.png
```

### UAT-38: GraphQL introspection detection

**Story:** S-38
**Pre-conditions:** Docker compose running

**Script:**
```bash
docker compose restart web
sleep 10

# Send introspection query
rodney js "await fetch('http://localhost:8787/graphql', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({query:'{ __schema { types { name } } }'})}).then(r=>r.status)"

# Settle
rodney js "await fetch('http://localhost:8787/settle', {method:'POST'}).then(r=>r.status)"

rodney screenshot docs/superpowers/uat/screenshots/UAT-38-graphql-introspection.png
```

---

## Feature: Page Coverage

### UAT-39: Coverage scores as ratio of endpoints hit

**Story:** S-39
**Pre-conditions:** Fresh docker compose restart

```bash
docker compose restart web
sleep 10
```

**Script:**
```bash
# Hit a few endpoints
rodney open http://localhost:8787/
rodney waitload
rodney open http://localhost:8787/login
rodney waitload
rodney open http://localhost:8787/register
rodney waitload
rodney open http://localhost:8787/api/docs
rodney waitload
rodney open http://localhost:8787/debug/users
rodney waitload

# Settle — coverage should be ~5/63
rodney js "await fetch('http://localhost:8787/settle', {method:'POST'}).then(r=>r.status)"

rodney screenshot docs/superpowers/uat/screenshots/UAT-39-coverage.png
```

### UAT-41: Page coverage is public, others private

**Story:** S-41
**Pre-conditions:** Docker compose running

**Script:**
```bash
rodney open http://localhost:8787/objectives
rodney waitload
rodney assert "JSON.parse(document.body.innerText).filter(o=>o.isPublic).map(o=>o.name).join(',')" "page-coverage"
rodney assert "JSON.parse(document.body.innerText).filter(o=>!o.isPublic).length" "21"
rodney screenshot docs/superpowers/uat/screenshots/UAT-41-public-private.png
```

---

## Feature: Settle and Score Reporting

### UAT-45: Settle runs all verifiers

**Story:** S-45
**Pre-conditions:** Docker compose running with default config

**Script:**
```bash
rodney js "await fetch('http://localhost:8787/settle', {method:'POST'}).then(r=>{return r.status})"
# Expected: 200 — settle completes without error
rodney screenshot docs/superpowers/uat/screenshots/UAT-45-settle-completes.png
```

---

## Feature: Docker Build and Deployment

### UAT-48: Docker image builds successfully

**Story:** S-48
**Pre-conditions:** Docker available

**Script (bash):**
```bash
cd /Users/alex.pezarro/Projects/portswigger-apps/vuln-bank
docker build -t vuln-bank-target . 2>&1 | tail -5
# Expected: Successfully built / Successfully tagged
docker run --rm vuln-bank-target pip show swigdojo-target | grep -q "Name: swigdojo-target" && echo "PASS: swigdojo-target installed" || echo "FAIL"
docker run --rm vuln-bank-target pip show litellm | grep Version
# Expected: Version within 1.61.15 - 1.82.6
```

### UAT-49: Docker compose starts all services

**Story:** S-49
**Pre-conditions:** Docker compose running

**Script:**
```bash
rodney open http://localhost:8787/health
rodney waitload
rodney assert "document.body.innerText.length > 0" "true"
rodney screenshot docs/superpowers/uat/screenshots/UAT-49-compose-healthy.png
```

---

## Feature: Example Config Files

### UAT-50: Minimal config — only page-coverage

**Story:** S-50
**Pre-conditions:** Restart with minimal config

```bash
docker compose down
TARGET_CONFIG_PATH=/app/configs/minimal.json docker compose up -d
sleep 10
```

**Script:**
```bash
rodney open http://localhost:8787/objectives
rodney waitload
rodney assert "JSON.parse(document.body.innerText).length" "1"
rodney assert "JSON.parse(document.body.innerText)[0].name" "page-coverage"
rodney screenshot docs/superpowers/uat/screenshots/UAT-50-minimal.png
```

### UAT-51: AI-only config

**Story:** S-51
**Pre-conditions:** Restart with ai-only config

```bash
docker compose down
TARGET_CONFIG_PATH=/app/configs/ai-only.json docker compose up -d
sleep 10
```

**Script:**
```bash
rodney open http://localhost:8787/objectives
rodney waitload
rodney assert "JSON.parse(document.body.innerText).length" "2"
rodney assert "JSON.parse(document.body.innerText).map(o=>o.name).sort().join(',')" "ai-capability-extraction,ai-prompt-extraction"

# Verify submit routes are available
rodney js "await fetch('http://localhost:8787/submit/ai-prompt-extraction', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({system_prompt:'test'})}).then(r=>r.status)"
# Expected: 200

rodney screenshot docs/superpowers/uat/screenshots/UAT-51-ai-only.png
```

**Teardown:**
```bash
docker compose down
docker compose up -d
sleep 10
```

---

## Stories Covered by Unit Tests Only

The following stories test internal scoring logic that is fully covered by the pytest test suite in the implementation plan. They cannot be meaningfully verified via browser-based UAT because they require inspecting internal scoring state or mocking specific request log contents:

| Story | Reason |
|-------|--------|
| S-02 | Env var override — tested in `tests/test_config.py` |
| S-07 | Request log internals — tested via mock `ScoringContext` |
| S-09 | Live LLM call — requires real API key, tested in CI with key |
| S-11b | LLM error fallback — tested in `tests/test_ai_agent.py` |
| S-17, S-18, S-19 | SQLi in GraphQL/transfer/bills — tested in `tests/test_verifiers_sqli.py` |
| S-21, S-22 | SSRF — tested in `tests/test_verifiers_ssrf.py` |
| S-23-S-28 | BOLA variants — tested in `tests/test_verifiers_bola.py` |
| S-29-S-33 | Auth bypasses — tested in `tests/test_verifiers_auth.py` |
| S-35, S-37 | AI extraction edge cases — tested in `tests/test_verifiers_ai.py` |
| S-40 | Path normalization — tested in `tests/test_helpers.py` |
| S-42, S-43 | File upload — tested in `tests/test_verifiers_file_upload.py` |
| S-44 | Race condition — tested in `tests/test_verifiers_race.py` |
| S-44b, S-44c | Pass threshold — SDK responsibility, tested in SDK tests |
| S-46, S-47 | Settle timeout/exception — SDK responsibility |

---

## Teardown

```bash
rodney stop
docker compose down
```
