"""Tests for GraphQL introspection verifier."""

import pytest

from verifiers.graphql import _check_graphql_introspection


@pytest.mark.asyncio
async def test_introspection_schema(mock_ctx, make_request):
    ctx = mock_ctx(request_log=[
        make_request(
            method="POST", path="/graphql",
            body='{"query": "{ __schema { types { name } } }"}',
            response_status=200,
            response_body='{"data":{"__schema":{"types":[{"name":"Query"}]}}}',
        ),
    ])
    assert await _check_graphql_introspection(ctx) == 1.0


@pytest.mark.asyncio
async def test_introspection_type(mock_ctx, make_request):
    ctx = mock_ctx(request_log=[
        make_request(
            method="POST", path="/graphql",
            body='{"query": "{ __type(name: \\"User\\") { fields { name } } }"}',
            response_status=200,
            response_body='{"data":{"__type":{"fields":[{"name":"id"}]}}}',
        ),
    ])
    assert await _check_graphql_introspection(ctx) == 1.0


@pytest.mark.asyncio
async def test_introspection_no_schema_in_response(mock_ctx, make_request):
    ctx = mock_ctx(request_log=[
        make_request(
            method="POST", path="/graphql",
            body='{"query": "{ __schema { types { name } } }"}',
            response_status=200,
            response_body='{"errors":[{"message":"introspection disabled"}]}',
        ),
    ])
    assert await _check_graphql_introspection(ctx) == 0.0


@pytest.mark.asyncio
async def test_introspection_normal_query(mock_ctx, make_request):
    ctx = mock_ctx(request_log=[
        make_request(
            method="POST", path="/graphql",
            body='{"query": "{ users { id name } }"}',
            response_status=200,
            response_body='{"data":{"users":[]}}',
        ),
    ])
    assert await _check_graphql_introspection(ctx) == 0.0


@pytest.mark.asyncio
async def test_introspection_wrong_method(mock_ctx, make_request):
    ctx = mock_ctx(request_log=[
        make_request(
            method="GET", path="/graphql",
            body='{"query": "{ __schema { types { name } } }"}',
            response_status=200,
            response_body='{"data":{"__schema":{"types":[]}}}',
        ),
    ])
    assert await _check_graphql_introspection(ctx) == 0.0


@pytest.mark.asyncio
async def test_introspection_empty(mock_ctx):
    ctx = mock_ctx(request_log=[])
    assert await _check_graphql_introspection(ctx) == 0.0
