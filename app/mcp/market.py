import yfinance as yf

def get_quote(ticker: str):
    """Fetch stock quote from yfinance"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            "ticker": ticker.upper(),
            "price": info.get("regularMarketPrice", 0),
            "change_pct": info.get("regularMarketChangePercent", 0),
            "currency": info.get("currency", "USD")
        }
    except Exception as e:
        return {
            "ticker": ticker.upper(),
            "price": 0,
            "change_pct": 0,
            "currency": "USD",
            "error": str(e)
        }

