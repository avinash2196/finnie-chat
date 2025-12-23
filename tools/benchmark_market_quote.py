import sys
import time
import statistics
import json

# Ensure project root on path
sys.path.append(r"C:\Users\avina\Codes\finnie-chat")

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Symbol sets
SMALL = ["AAPL", "MSFT", "NVDA"]
MEDIUM = ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "META"]
LARGE = [
    "NVDA", "TSLA", "AAPL", "MSFT", "AMZN", "META", "GOOGL", "AMD",
    "NFLX", "PYPL", "INTC", "BA", "DIS", "JNJ", "V", "PG",
    "XOM", "WMT", "JPM", "GS"
]

ITERATIONS = 30
PAUSE = 0.05

RESULTS = {}


def run_set(name, symbols):
    times = []
    successes = 0
    for i in range(ITERATIONS):
        t0 = time.monotonic()
        resp = client.post("/market/quote", json={"symbols": symbols})
        dt = (time.monotonic() - t0) * 1000
        times.append(dt)
        if resp.status_code == 200:
            successes += 1
        time.sleep(PAUSE)
    # compute stats
    p50 = statistics.median(times)
    p95 = sorted(times)[int(len(times) * 0.95) - 1]
    avg = statistics.mean(times)
    RESULTS[name] = {
        "count": ITERATIONS,
        "successes": successes,
        "p50_ms": p50,
        "p95_ms": p95,
        "avg_ms": avg,
        "all_ms": times
    }
    print(f"{name}: p50={p50:.1f}ms p95={p95:.1f}ms avg={avg:.1f}ms success={successes}/{ITERATIONS}")


if __name__ == "__main__":
    print("Starting benchmark: iterations=", ITERATIONS)
    run_set("small", SMALL)
    run_set("medium", MEDIUM)
    run_set("large", LARGE)

    # Save results
    with open("benchmark_market_quote_results.json", "w", encoding="utf-8") as f:
        json.dump(RESULTS, f, indent=2)
    print("Wrote benchmark_market_quote_results.json")
