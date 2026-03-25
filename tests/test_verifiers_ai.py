"""Tests for AI extraction verifiers."""

import pytest

from verifiers.ai_extraction import (
    _check_ai_prompt_extraction,
    _check_ai_capability_extraction,
    _capability_matches,
    KNOWN_CAPABILITIES,
)


# --- Prompt Extraction ---

@pytest.mark.asyncio
async def test_prompt_exact_match(mock_ctx):
    prompt = "You are VulnBank AI assistant. Help users with banking."
    config = {"llm": {"system_prompt": prompt}}
    ctx = mock_ctx(stored={"submission:ai-prompt-extraction": {"system_prompt": prompt}})
    score = await _check_ai_prompt_extraction(ctx, config)
    assert score == 1.0


@pytest.mark.asyncio
async def test_prompt_partial_match(mock_ctx):
    actual = "You are VulnBank AI assistant. Help users with banking queries."
    submitted = "You are VulnBank AI assistant."
    config = {"llm": {"system_prompt": actual}}
    ctx = mock_ctx(stored={"submission:ai-prompt-extraction": {"system_prompt": submitted}})
    score = await _check_ai_prompt_extraction(ctx, config)
    assert 0.5 < score < 1.0


@pytest.mark.asyncio
async def test_prompt_empty_submission(mock_ctx):
    config = {"llm": {"system_prompt": "actual prompt"}}
    ctx = mock_ctx(stored={"submission:ai-prompt-extraction": {"system_prompt": ""}})
    assert await _check_ai_prompt_extraction(ctx, config) == 0.0


@pytest.mark.asyncio
async def test_prompt_no_submission(mock_ctx):
    config = {"llm": {"system_prompt": "actual prompt"}}
    ctx = mock_ctx(stored={})
    assert await _check_ai_prompt_extraction(ctx, config) == 0.0


@pytest.mark.asyncio
async def test_prompt_no_actual(mock_ctx):
    config = {"llm": {}}
    ctx = mock_ctx(stored={"submission:ai-prompt-extraction": {"system_prompt": "something"}})
    assert await _check_ai_prompt_extraction(ctx, config) == 0.0


# --- Capability Extraction ---

@pytest.mark.asyncio
async def test_capabilities_all_matched(mock_ctx):
    config = {}
    ctx = mock_ctx(stored={
        "submission:ai-capability-extraction": {
            "capabilities": list(KNOWN_CAPABILITIES),
        }
    })
    score = await _check_ai_capability_extraction(ctx, config)
    assert score == 1.0


@pytest.mark.asyncio
async def test_capabilities_partial(mock_ctx):
    config = {}
    ctx = mock_ctx(stored={
        "submission:ai-capability-extraction": {
            "capabilities": ["query-all-users", "query-schema", "query-balance"],
        }
    })
    score = await _check_ai_capability_extraction(ctx, config)
    assert score == 3 / len(KNOWN_CAPABILITIES)


@pytest.mark.asyncio
async def test_capabilities_substring_match(mock_ctx):
    config = {}
    ctx = mock_ctx(stored={
        "submission:ai-capability-extraction": {
            "capabilities": ["the bot can query-all-users from the database"],
        }
    })
    score = await _check_ai_capability_extraction(ctx, config)
    assert score >= 1 / len(KNOWN_CAPABILITIES)


@pytest.mark.asyncio
async def test_capabilities_empty(mock_ctx):
    config = {}
    ctx = mock_ctx(stored={"submission:ai-capability-extraction": {"capabilities": []}})
    assert await _check_ai_capability_extraction(ctx, config) == 0.0


@pytest.mark.asyncio
async def test_capabilities_no_submission(mock_ctx):
    config = {}
    ctx = mock_ctx(stored={})
    assert await _check_ai_capability_extraction(ctx, config) == 0.0


# --- Capability Match Helper ---

def test_capability_matches_exact():
    assert _capability_matches("query-all-users", "query-all-users")


def test_capability_matches_substring():
    assert _capability_matches("can query-all-users from db", "query-all-users")


def test_capability_matches_case_insensitive():
    assert _capability_matches("Query-All-Users", "query-all-users")


def test_capability_no_match():
    assert not _capability_matches("something-else", "query-all-users")
