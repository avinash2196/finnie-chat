"""Quick diagnostic script to test news MCP with general headlines.
Run this to verify the news path works end-to-end.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.env import load_env_once
load_env_once()

# Set debug logging
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

print("\n" + "="*80)
print("QUICK NEWS MCP DIAGNOSTIC")
print("="*80)

# Test 1: General news (no tickers)
print("\n[TEST 1] General market headlines (no tickers)")
print("-" * 80)

from app.agents.news_synthesizer import run as news_run

message = "Show me market headlines"
print(f"Message: {message}")
print("\nCalling news_synthesizer...\n")

result = news_run(message)

print("\n" + "="*80)
print("RESULT:")
print("="*80)
print(result)
print("\n" + "="*80)

# Test 2: Ticker-specific news
print("\n[TEST 2] Ticker-specific news")
print("-" * 80)

message2 = "Latest AAPL news"
print(f"Message: {message2}")
print("\nCalling news_synthesizer...\n")

result2 = news_run(message2)

print("\n" + "="*80)
print("RESULT:")
print("="*80)
print(result2)
print("\n" + "="*80)

# Test 3: Full orchestrator
print("\n[TEST 3] Full orchestrator path")
print("-" * 80)

from app.agents.orchestrator import handle_message

message3 = "What are the latest market headlines?"
print(f"Message: {message3}")
print("\nCalling orchestrator...\n")

reply, intent, risk = handle_message(message3, user_id="user_123")

print("\n" + "="*80)
print(f"Intent: {intent}")
print(f"Risk: {risk}")
print("REPLY:")
print("="*80)
print(reply)
print("\n" + "="*80)
