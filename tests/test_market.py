"""
Tests for market MCP server and client.
"""

import pytest
from unittest.mock import Mock, patch
from app.mcp.market import MarketClient, MarketQuote, get_client
from app.mcp.market_server import MarketMCPServer, GetQuoteTool


def test_get_quote_tool_schema():
    """Test GetQuoteTool schema generation."""
    tool = GetQuoteTool()
    schema = tool.to_schema()
    
    assert schema["name"] == "get_quote"
    assert "ticker" in schema["inputSchema"]["properties"]
    assert "ticker" in schema["inputSchema"]["required"]


def test_market_mcp_server_tools():
    """Test MarketMCPServer lists available tools."""
    server = MarketMCPServer()
    tools = server.get_tools()
    
    assert len(tools) > 0
    assert any(t["name"] == "get_quote" for t in tools)


def test_market_quote_dataclass():
    """Test MarketQuote dataclass."""
    quote = MarketQuote(
        ticker="AAPL",
        price=150.0,
        currency="USD",
        change_pct=2.5,
        timestamp=1234567890.0
    )
    
    assert quote.ticker == "AAPL"
    assert quote.price == 150.0
    assert quote.change_pct == 2.5
    assert quote.error is None


def test_market_client_caching():
    """Test MarketClient caches quotes."""
    client = MarketClient(ttl_seconds=60)
    
    # Mock the server
    with patch.object(client._server, 'call_tool') as mock_tool:
        mock_tool.return_value = {
            "ticker": "SPY",
            "price": 450.0,
            "currency": "USD",
            "change_pct": 1.0
        }
        
        # First call should hit the server
        quote1 = client.get_quote("SPY")
        assert quote1.price == 450.0
        assert mock_tool.call_count == 1
        
        # Second call should use cache
        quote2 = client.get_quote("SPY")
        assert quote2.price == 450.0
        assert mock_tool.call_count == 1  # Still 1, not 2


def test_market_client_error_handling():
    """Test MarketClient handles errors gracefully."""
    client = MarketClient()
    
    with patch.object(client._server, 'call_tool') as mock_tool:
        mock_tool.side_effect = Exception("API Error")
        
        quote = client.get_quote("INVALID")
        assert quote.price is None
        assert quote.error is not None
        assert "API Error" in quote.error


def test_get_client_singleton():
    """Test get_client returns singleton."""
    client1 = get_client()
    client2 = get_client()
    
    assert client1 is client2


@patch('yfinance.Ticker')
def test_get_quote_tool_execute_success(mock_ticker):
    """Test GetQuoteTool executes successfully with mock yfinance."""
    mock_ticker_instance = Mock()
    mock_ticker_instance.info = {
        "regularMarketPrice": 150.0,
        "regularMarketPreviousClose": 145.0,
        "currency": "USD"
    }
    mock_ticker.return_value = mock_ticker_instance
    
    tool = GetQuoteTool()
    result = tool.execute("AAPL")
    
    assert result["ticker"] == "AAPL"
    assert result["price"] == 150.0
    assert result["currency"] == "USD"
    assert result["change_pct"] == pytest.approx(3.45, 0.01)


@patch('yfinance.Ticker')
def test_get_quote_tool_execute_error(mock_ticker):
    """Test GetQuoteTool handles errors."""
    mock_ticker.side_effect = Exception("Connection error")
    
    tool = GetQuoteTool()
    result = tool.execute("INVALID")
    
    assert result["ticker"] == "INVALID"
    assert result["price"] is None
    assert result["error"] is not None
