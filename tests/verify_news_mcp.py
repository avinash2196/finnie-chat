"""Manual verification script for News MCP functionality.
Run this to verify Alpha Vantage API integration and trace actual calls.

Usage:
    python tests/verify_news_mcp.py

Requires:
    - ALPHA_VANTAGE_API_KEY in .env
    - Active internet connection
"""
import os
import sys
import logging
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from app.env import load_env_once
load_env_once()

from app.mcp.news_server import get_server as get_news_server
from app.mcp.news import get_client as get_news_client
from app.agents.news_synthesizer import run as news_synthesizer_run


def test_mcp_server_direct():
    """Test 1: Direct MCP server call"""
    print("\n" + "="*80)
    print("TEST 1: Direct MCP Server Call")
    print("="*80)
    
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        print("❌ ALPHA_VANTAGE_API_KEY not set in environment")
        return False
    
    print(f"✓ API Key found: {api_key[:10]}...")
    
    server = get_news_server()
    print("✓ News MCP server instantiated")
    
    tickers = ["AAPL", "MSFT"]
    print(f"\n📡 Calling MCP server with tickers: {tickers}")
    
    try:
        result = server.call_tool("get_news", {"tickers": tickers, "limit": 3})
        
        print(f"\n📥 Response received:")
        print(f"   Error: {result.get('error')}")
        print(f"   Article count: {len(result.get('articles', []))}")
        print(f"   Source: {result.get('source')}")
        
        if result.get("articles"):
            print(f"\n📰 Sample article:")
            article = result["articles"][0]
            print(f"   Title: {article.get('title')}")
            print(f"   Source: {article.get('source')}")
            print(f"   Tickers: {article.get('tickers')}")
            print(f"   URL: {article.get('url')}")
            return True
        else:
            print("⚠️  No articles returned (might be rate limit or no news)")
            print(f"   Full response: {result}")
            return False
            
    except Exception as e:
        print(f"❌ MCP server call failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mcp_client():
    """Test 2: MCP client with caching"""
    print("\n" + "="*80)
    print("TEST 2: MCP Client (with caching)")
    print("="*80)
    
    client = get_news_client()
    print("✓ News MCP client instantiated")
    
    tickers = ["TSLA"]
    print(f"\n📡 Calling MCP client with tickers: {tickers}")
    
    try:
        # First call (should hit server)
        articles = client.get_news(tickers, limit=2)
        print(f"\n📥 First call - Articles received: {len(articles)}")
        
        if articles:
            print(f"\n📰 Sample article:")
            article = articles[0]
            print(f"   Title: {article.title}")
            print(f"   Source: {article.source}")
            print(f"   Tickers: {article.tickers}")
        
        # Second call (should hit cache)
        print(f"\n🔄 Making second call (should use cache)...")
        articles2 = client.get_news(tickers, limit=2)
        print(f"   Articles from cache: {len(articles2)}")
        
        return len(articles) > 0
        
    except Exception as e:
        print(f"❌ MCP client call failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_news_agent():
    """Test 3: Full news synthesizer agent"""
    print("\n" + "="*80)
    print("TEST 3: News Synthesizer Agent")
    print("="*80)
    
    test_messages = [
        "Show me latest headlines for AAPL",
        "What's the news on Tesla stock?",
        "NVDA earnings report summary",
    ]
    
    results = []
    for message in test_messages:
        print(f"\n📝 Message: {message}")
        
        try:
            response = news_synthesizer_run(message)
            print(f"\n📤 Agent response ({len(response)} chars):")
            print(f"   Preview: {response[:200]}...")
            
            # Check for key elements
            has_summary = "News Summary" in response
            has_citations = "Citations" in response
            has_timestamp = "Timestamp" in response
            
            print(f"\n✓ Contains summary section: {has_summary}")
            print(f"✓ Contains citations: {has_citations}")
            print(f"✓ Contains timestamp: {has_timestamp}")
            
            results.append(len(response) > 100)
            
        except Exception as e:
            print(f"❌ Agent call failed: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    return all(results)


def test_orchestrator_integration():
    """Test 4: Full orchestrator integration"""
    print("\n" + "="*80)
    print("TEST 4: Orchestrator Integration (ASK_NEWS intent)")
    print("="*80)
    
    from app.agents.orchestrator import handle_message
    
    message = "What are the latest market headlines for Apple?"
    print(f"\n📝 Message: {message}")
    
    try:
        reply, intent, risk = handle_message(message, user_id="user_123")
        
        print(f"\n📤 Orchestrator response:")
        print(f"   Intent: {intent}")
        print(f"   Risk: {risk}")
        print(f"   Reply length: {len(reply)} chars")
        print(f"   Preview: {reply[:300]}...")
        
        # Check if news content is present
        has_content = len(reply) > 100
        not_blocked = "don't have enough" not in reply.lower()
        
        print(f"\n✓ Has substantial content: {has_content}")
        print(f"✓ Not blocked by synthesis: {not_blocked}")
        
        return has_content and not_blocked
        
    except Exception as e:
        print(f"❌ Orchestrator call failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all verification tests"""
    print("\n" + "="*80)
    print("NEWS MCP VERIFICATION SUITE")
    print("="*80)
    print(f"Python: {sys.version}")
    print(f"Working dir: {os.getcwd()}")
    
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if api_key:
        print(f"✓ ALPHA_VANTAGE_API_KEY: {api_key[:10]}...{api_key[-4:]}")
    else:
        print("❌ ALPHA_VANTAGE_API_KEY not found")
        print("\nPlease set ALPHA_VANTAGE_API_KEY in .env file")
        return 1
    
    results = {
        "MCP Server Direct": test_mcp_server_direct(),
        "MCP Client": test_mcp_client(),
        "News Agent": test_news_agent(),
        "Orchestrator": test_orchestrator_integration(),
    }
    
    print("\n" + "="*80)
    print("VERIFICATION SUMMARY")
    print("="*80)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 All verification tests passed!")
        return 0
    else:
        failed = [name for name, passed in results.items() if not passed]
        print(f"\n⚠️  Failed tests: {', '.join(failed)}")
        print("\nDebugging tips:")
        print("1. Check LangSmith dashboard for detailed traces")
        print("2. Review app logs for [NEWS_MCP] and [NEWS_AGENT] messages")
        print("3. Verify Alpha Vantage API key and rate limits")
        print("4. Ensure internet connectivity for API calls")
        return 1


if __name__ == "__main__":
    sys.exit(main())
