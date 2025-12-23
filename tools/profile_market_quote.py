import sys
import time
import io
import cProfile
import pstats

# Ensure project root is on path when run from tools
sys.path.append(r"C:\Users\avina\Codes\finnie-chat")

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

SYMBOLS = ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "META"]
ITERATIONS = 5


def run_requests():
    for i in range(ITERATIONS):
        print(f"Request {i+1}/{ITERATIONS}")
        resp = client.post("/market/quote", json={"symbols": SYMBOLS})
        print("status", resp.status_code, "quotes", len(resp.json().get("quotes", {})))
        # small gap between requests
        time.sleep(0.2)


if __name__ == "__main__":
    pr = cProfile.Profile()
    pr.enable()
    start = time.time()
    try:
        run_requests()
    finally:
        duration = time.time() - start
        pr.disable()

    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).strip_dirs().sort_stats("cumtime")
    ps.print_stats(50)

    out = s.getvalue()
    print("\n=== Profiling Summary (top 50 by cumulative time) ===\n")
    print(out)

    # Save to file for deeper inspection
    with open("profile_market_quote.txt", "w", encoding="utf-8") as f:
        f.write(f"Total run time: {duration:.3f}s\n\n")
        f.write(out)

    print("Wrote profile_market_quote.txt")
