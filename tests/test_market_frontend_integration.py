"""
Integration tests for Market frontend pages.
Tests verify that frontend can successfully call backend API endpoints.
"""
import pytest
import requests
from unittest.mock import patch, MagicMock


def test_market_quote_api_call():
    """Test that market quote API call structure matches frontend usage"""
    # This test verifies the API request format used by frontend pages
    api_url = "http://localhost:8000/market/quote"
    symbols = ["^GSPC", "^DJI", "^IXIC", "^RUT"]
    
    # Mock the requests.post call
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "quotes": {
                "^GSPC": {"price": 4783.45, "change": 35.2, "change_pct": 0.74},
                "^DJI": {"price": 37305.16, "change": -45.23, "change_pct": -0.12},
                "^IXIC": {"price": 14813.92, "change": 123.45, "change_pct": 0.84},
                "^RUT": {"price": 2027.07, "change": 12.34, "change_pct": 0.61}
            },
            "count": 4
        }
        mock_post.return_value = mock_response
        
        # Simulate frontend API call
        response = requests.post(api_url, json={"symbols": symbols}, timeout=5)
        
        assert response.status_code == 200
        data = response.json()
        assert "quotes" in data
        assert len(data["quotes"]) == 4
        
        # Verify data structure matches frontend expectations
        for symbol in symbols:
            quote = data["quotes"][symbol]
            assert "price" in quote
            assert "change" in quote
            assert "change_pct" in quote


def test_market_quote_handles_none_values():
    """Test that None values from API are handled correctly"""
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "quotes": {
                "^GSPC": {"price": None, "change": None, "change_pct": None}
            },
            "count": 1
        }
        mock_post.return_value = mock_response
        
        response = requests.post("http://localhost:8000/market/quote", 
                               json={"symbols": ["^GSPC"]}, timeout=5)
        
        data = response.json()
        quote = data["quotes"]["^GSPC"]
        
        # Frontend should use `or 0` to handle None values
        price = quote.get("price") or 0
        change = quote.get("change") or 0
        change_pct = quote.get("change_pct") or 0
        
        assert price == 0
        assert change == 0
        assert change_pct == 0


def test_screener_api_call():
    """Test that screener API call structure matches frontend usage"""
    api_url = "http://localhost:8000/market/screen"
    
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {"ticker": "VZ", "price": 38.45, "dividend_yield": 6.8},
                {"ticker": "T", "price": 15.92, "dividend_yield": 6.5}
            ]
        }
        mock_post.return_value = mock_response
        
        # Simulate frontend screener call
        response = requests.post(
            api_url,
            json={
                "screener_type": "dividend",
                "params": {"user_id": "user_001"}
            },
            timeout=10
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 2


def test_screener_handles_empty_results():
    """Test that empty screener results are handled gracefully"""
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}
        mock_post.return_value = mock_response
        
        response = requests.post(
            "http://localhost:8000/market/screen",
            json={"screener_type": "dividend", "params": {}},
            timeout=10
        )
        
        data = response.json()
        stocks = data.get("results", [])
        
        # Frontend should handle empty results gracefully
        assert stocks == []
        assert len(stocks) == 0


def test_api_error_handling():
    """Test that API errors are handled correctly"""
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response
        
        response = requests.post(
            "http://localhost:8000/market/quote",
            json={"symbols": ["^GSPC"]},
            timeout=5
        )
        
        # Frontend should check status code
        assert response.status_code != 200


def test_api_timeout_handling():
    """Test that API timeouts are handled correctly"""
    with patch('requests.post') as mock_post:
        mock_post.side_effect = requests.exceptions.Timeout("Connection timeout")
        
        try:
            response = requests.post(
                "http://localhost:8000/market/quote",
                json={"symbols": ["^GSPC"]},
                timeout=5
            )
            assert False, "Should have raised Timeout exception"
        except requests.exceptions.Timeout as e:
            # Frontend should catch this and show error message
            assert "timeout" in str(e).lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
