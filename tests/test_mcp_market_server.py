import types
from types import SimpleNamespace
import pytest

from app.mcp import market_server


def test_get_quote_tool_success(monkeypatch):
    # Mock yfinance.Ticker to return an object with .info
    class MockTicker:
        def __init__(self, ticker):
            self.info = {
                "regularMarketPrice": 123.45,
                "regularMarketPreviousClose": 120.0,
                "currency": "USD",
                "regularMarketTime": 1600000000
            }

    monkeypatch.setattr(market_server.yf, "Ticker", MockTicker)

    tool = market_server.GetQuoteTool()
    res = tool.execute("AAPL")
    assert res["ticker"] == "AAPL"
    assert res["price"] == 123.45
    assert isinstance(res.get("change_pct"), float)


def test_get_quote_tool_exception(monkeypatch):
    # Simulate yfinance raising on Ticker creation
    def raise_ticker(ticker):
        raise RuntimeError("yfinance fail")

    monkeypatch.setattr(market_server.yf, "Ticker", raise_ticker)
    tool = market_server.GetQuoteTool()
    res = tool.execute("FOO")
    assert res["price"] is None
    assert "error" in res


def test_get_quotes_tool_batch_success(monkeypatch):
    # Mock yfinance.Tickers to provide a .tickers mapping
    class MockSingle:
        def __init__(self, info):
            self.info = info

    class MockMulti:
        def __init__(self, symbols):
            # create tickers mapping with info per symbol
            self.tickers = {}
            for s in symbols.split():
                if s == "AAPL":
                    info = {"regularMarketPrice": 400.0, "regularMarketPreviousClose": 360.0, "currency": "USD", "regularMarketTime": 160}
                else:
                    info = {"regularMarketPrice": None, "regularMarketPreviousClose": None, "currency": "USD", "regularMarketTime": None}
                self.tickers[s] = MockSingle(info)

    monkeypatch.setattr(market_server.yf, "Tickers", MockMulti)

    tool = market_server.GetQuotesTool()
    out = tool.execute(["AAPL", "FAKE"])
    assert "AAPL" in out and "FAKE" in out
    assert out["AAPL"]["price"] == 400.0
    assert out["AAPL"]["change_pct"] is not None
    assert out["FAKE"]["price"] is None


def test_get_quotes_tool_handles_per_ticker_exceptions(monkeypatch):
    # Mock tickers where accessing info raises
    class BadTicker:
        @property
        def info(self):
            raise RuntimeError("bad info")

    class MockMultiBad:
        def __init__(self, symbols):
            self.tickers = {s: BadTicker() for s in symbols.split()}

    monkeypatch.setattr(market_server.yf, "Tickers", MockMultiBad)

    tool = market_server.GetQuotesTool()
    out = tool.execute(["BAD1", "BAD2"])
    # Should return entries with price None and an error key
    assert out["BAD1"]["price"] is None
    assert "error" in out["BAD1"]


def test_market_mcp_server_tools_and_call_tool():
    srv = market_server.MarketMCPServer()
    tools = srv.get_tools()
    names = {t["name"] for t in tools}
    assert "get_quote" in names and "get_quotes" in names

    # call existing tool
    res = srv.call_tool("get_quote", {"ticker": "AAPL"})
    assert isinstance(res, dict)

    # calling missing tool raises
    with pytest.raises(ValueError):
        srv.call_tool("no_such", {})
