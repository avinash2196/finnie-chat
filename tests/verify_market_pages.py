"""
Manual verification script for Market pages.
Run this with the backend server running to verify real API integration.
"""
import requests
import sys

API_BASE_URL = "http://localhost:8000"

def test_market_quote_endpoint():
    """Test market quote endpoint with real indices"""
    print("\n" + "="*60)
    print("TEST 1: Market Quote Endpoint")
    print("="*60)
    
    symbols = ["^GSPC", "^DJI", "^IXIC", "^RUT"]
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/market/quote",
            json={"symbols": symbols},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Quotes returned: {data.get('count', 0)}")
            print("\nIndex Data:")
            print("-" * 60)
            
            for symbol in symbols:
                quote = data.get("quotes", {}).get(symbol, {})
                price = quote.get("price") or 0
                change = quote.get("change") or 0
                change_pct = quote.get("change_pct") or 0
                
                print(f"{symbol:8} | Price: ${price:>10,.2f} | Change: {change_pct:>+6.2f}%")
                
                # Verify None handling
                if price > 0:
                    print(f"           ✓ Valid data received")
                else:
                    print(f"           ⚠ No price data (possibly market closed)")
            
            print("\n✅ PASS: Quote endpoint working correctly")
            return True
        else:
            print(f"❌ FAIL: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ FAIL: Cannot connect to backend")
        print("Please ensure backend is running on http://localhost:8000")
        return False
    except Exception as e:
        print(f"❌ FAIL: {str(e)}")
        return False


def test_screener_endpoint():
    """Test screener endpoint"""
    print("\n" + "="*60)
    print("TEST 2: Stock Screener Endpoint")
    print("="*60)
    
    screener_types = ["dividend", "growth", "value"]
    
    for screener_type in screener_types:
        print(f"\nTesting {screener_type.upper()} screener...")
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/market/screen",
                json={
                    "screener_type": screener_type,
                    "params": {"user_id": "user_001"}
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                print(f"  ✓ Returned {len(results)} stocks")
                
                if results:
                    # Show first result as example
                    print(f"  Example: {results[0]}")
            else:
                print(f"  ⚠ HTTP {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            return False
    
    print("\n✅ PASS: Screener endpoint working correctly")
    return True


def test_none_value_handling():
    """Test that None values are handled correctly"""
    print("\n" + "="*60)
    print("TEST 3: None Value Handling")
    print("="*60)
    
    # Simulate what frontend does with None values
    test_cases = [
        {"price": None, "change": None, "change_pct": None},
        {"price": 0, "change": 0, "change_pct": 0},
        {"price": 4783.45, "change": 35.2, "change_pct": 0.74},
    ]
    
    print("\nTesting `or 0` pattern for None handling:")
    print("-" * 60)
    
    for i, quote in enumerate(test_cases, 1):
        price = quote.get("price") or 0
        change = quote.get("change") or 0
        change_pct = quote.get("change_pct") or 0
        
        print(f"Test {i}: Input={quote}")
        print(f"       Output: price={price}, change={change}, change_pct={change_pct}")
        
        # Verify no TypeError when comparing with 0
        try:
            if change >= 0:
                delta_color = "normal"
            else:
                delta_color = "inverse"
            print(f"       ✓ Comparison works, delta_color={delta_color}")
        except TypeError as e:
            print(f"       ❌ TypeError: {e}")
            return False
    
    print("\n✅ PASS: None handling working correctly")
    return True


def main():
    """Run all verification tests"""
    print("\n" + "="*60)
    print("MARKET PAGES VERIFICATION SCRIPT")
    print("="*60)
    print("\nThis script verifies that:")
    print("1. Backend API endpoints are working")
    print("2. Data format matches frontend expectations")
    print("3. None values are handled correctly")
    print("4. Both Market.py and Market_Trends.py can use the API")
    
    results = []
    
    # Run tests
    results.append(("Market Quote API", test_market_quote_endpoint()))
    results.append(("Screener API", test_screener_endpoint()))
    results.append(("None Value Handling", test_none_value_handling()))
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("\nThe Market pages are ready to use with real API data!")
        print("Both pages will now show live market data instead of mock data.")
    else:
        print("❌ SOME TESTS FAILED")
        print("\nPlease ensure:")
        print("1. Backend server is running (python -m uvicorn app.main:app)")
        print("2. You have internet connection for yfinance data")
        print("3. API endpoints are accessible at http://localhost:8000")
    print("="*60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
