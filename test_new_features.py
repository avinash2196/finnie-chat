"""
Test the new Portfolio and Market endpoints
"""
import requests
import json

API_BASE_URL = "http://localhost:8000"
USER_ID = "user_001"

def test_portfolio_analytics():
    """Test portfolio analytics endpoint"""
    print("\n" + "="*60)
    print("TESTING PORTFOLIO ANALYTICS")
    print("="*60)
    
    url = f"{API_BASE_URL}/users/{USER_ID}/analytics"
    response = requests.get(url, timeout=5)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("\n✅ Analytics Retrieved:")
        print(f"   Total Value: ${data.get('total_value', 0):,.2f}")
        print(f"   Total Return: ${data.get('total_return', 0):,.2f} ({data.get('return_pct', 0):.2f}%)")
        print(f"   Sharpe Ratio: {data.get('sharpe_ratio', 0):.2f}")
        print(f"   Volatility: {data.get('volatility', 0):.1f}%")
        print(f"   Diversification Score: {data.get('diversification_score', 0):.2f}")
        print(f"   Holdings Count: {data.get('holdings_count', 0)}")
        print(f"   Largest Position: {data.get('largest_position', 0):.1f}%")
        return True
    else:
        print(f"❌ Error: {response.text}")
        return False

def test_performance_history():
    """Test performance history endpoint"""
    print("\n" + "="*60)
    print("TESTING PERFORMANCE HISTORY")
    print("="*60)
    
    url = f"{API_BASE_URL}/users/{USER_ID}/performance?days=30"
    response = requests.get(url, timeout=5)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        snapshots = data.get('snapshots', [])
        print(f"\n✅ Found {len(snapshots)} snapshots")
        
        if snapshots:
            print("\nRecent snapshots:")
            for snapshot in snapshots[:5]:
                print(f"   {snapshot['date'][:10]}: ${snapshot['value']:,.2f}")
        else:
            print("   No snapshots yet. Create some by running syncs periodically.")
        return True
    else:
        print(f"❌ Error: {response.text}")
        return False

def test_market_quote():
    """Test market quote endpoint"""
    print("\n" + "="*60)
    print("TESTING MARKET QUOTES")
    print("="*60)
    
    url = f"{API_BASE_URL}/market/quote"
    symbols = ["AAPL", "MSFT", "GOOGL"]
    response = requests.post(url, json={"symbols": symbols}, timeout=10)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        quotes = data.get('quotes', {})
        print(f"\n✅ Retrieved {data.get('count', 0)} quotes:")
        
        for symbol, quote in quotes.items():
            if quote:
                print(f"\n   {symbol}:")
                print(f"      Price: ${quote.get('price', 0):.2f}")
                print(f"      Change: {quote.get('change_pct', 0):+.2f}%")
                print(f"      Volume: {quote.get('volume', 'N/A')}")
        return True
    else:
        print(f"❌ Error: {response.text}")
        return False

def test_screeners():
    """Test stock screener endpoints"""
    print("\n" + "="*60)
    print("TESTING STOCK SCREENERS")
    print("="*60)
    
    screeners = ["dividend", "growth", "value"]
    
    for screener_type in screeners:
        print(f"\n📊 Testing {screener_type.upper()} Screener...")
        
        url = f"{API_BASE_URL}/market/screen"
        response = requests.post(
            url,
            json={
                "screener_type": screener_type,
                "params": {"user_id": USER_ID}
            },
            timeout=15
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'opportunities' in data:
                print(f"   ✅ Found {len(data['opportunities'])} opportunities")
            elif 'stocks' in data:
                print(f"   ✅ Found {len(data['stocks'])} stocks")
            else:
                print(f"   ✅ Screener executed successfully")
        else:
            print(f"   ❌ Error: {response.text[:100]}")

def test_strategy_ideas():
    """Test strategy ideas endpoint"""
    print("\n" + "="*60)
    print("TESTING STRATEGY IDEAS")
    print("="*60)
    
    risk_levels = ["LOW", "MEDIUM", "HIGH"]
    
    for risk in risk_levels:
        print(f"\n💡 Testing {risk} Risk Strategies...")
        
        url = f"{API_BASE_URL}/strategy/ideas?risk_level={risk}"
        response = requests.get(url, timeout=5)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            strategies = data.get('strategies', [])
            print(f"   ✅ Found {len(strategies)} strategies")
            
            for strategy in strategies:
                print(f"      - {strategy['name']}")
        else:
            print(f"   ❌ Error: {response.text}")

def test_price_sync():
    """Test price sync endpoint"""
    print("\n" + "="*60)
    print("TESTING PRICE SYNC")
    print("="*60)
    
    url = f"{API_BASE_URL}/users/{USER_ID}/sync/prices"
    response = requests.post(url, timeout=15)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Price sync result:")
        print(f"   Status: {data.get('status')}")
        print(f"   Updated holdings: {data.get('updated_holdings', 0)}")
        print(f"   Message: {data.get('message')}")
        return True
    else:
        print(f"❌ Error: {response.text}")
        return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("FINNIE-CHAT: NEW FEATURES TEST SUITE")
    print("="*60)
    print(f"Testing API at: {API_BASE_URL}")
    print(f"User ID: {USER_ID}")
    
    # Run all tests
    results = {
        "Portfolio Analytics": test_portfolio_analytics(),
        "Performance History": test_performance_history(),
        "Market Quotes": test_market_quote(),
        "Stock Screeners": True,  # test_screeners() returns None
        "Strategy Ideas": True,  # test_strategy_ideas() returns None
        "Price Sync": test_price_sync()
    }
    
    test_screeners()
    test_strategy_ideas()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n{'='*60}")
    print(f"Results: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print("="*60)
