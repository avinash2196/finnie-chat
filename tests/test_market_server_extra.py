"""Extra tests for Market MCP server singleton and error path."""

import pytest
from app.mcp.market_server import get_server


def test_get_server_singleton_instance():
    s1 = get_server()
    s2 = get_server()
    assert s1 is s2


def test_call_tool_not_found_raises():
    server = get_server()
    with pytest.raises(ValueError):
        server.call_tool('nonexistent', {})
