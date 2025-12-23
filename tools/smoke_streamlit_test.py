import time
import requests
import sys

BACKEND = "http://127.0.0.1:8000"
FRONTEND = "http://127.0.0.1:8501"

symbols = ["AAPL", "MSFT", "NVDA"]

def wait_for(url, timeout=20):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            r = requests.get(url, timeout=3)
            return True, r.status_code
        except Exception:
            time.sleep(0.5)
    return False, None

if __name__ == '__main__':
    print("Waiting for backend...", end=" ")
    ok, status = wait_for(BACKEND + "/docs", timeout=30)
    print("OK" if ok else "FAIL", status)
    if not ok:
        print("Backend did not start; aborting smoke test.")
        sys.exit(2)

    print("Waiting for frontend...", end=" ")
    ok_f, status_f = wait_for(FRONTEND, timeout=30)
    print("OK" if ok_f else "FAIL", status_f)

    # Measure /market/quote latency twice to observe short-lived aggregation cache behavior
    url = BACKEND + "/market/quote"
    for i in range(2):
        t0 = time.time()
        try:
            r = requests.post(url, json={"symbols": symbols}, timeout=10)
            dt = time.time() - t0
            print(f"Request {i+1}: status={r.status_code}, elapsed={dt:.3f}s")
            try:
                js = r.json()
                qcount = len(js.get('quotes', {}))
                print(f"  quotes returned: {qcount}")
            except Exception:
                print("  invalid JSON response")
        except Exception as e:
            print(f"Request {i+1} failed: {e}")
        time.sleep(1)

    # Quick check: try hitting the Streamlit page for the Market route
    try:
        r = requests.get(FRONTEND + "/?page=2_%F0%9F%93%88_Market", timeout=5)
        print("Frontend page GET:", r.status_code)
    except Exception as e:
        print("Frontend page GET failed:", e)

    print("Smoke test completed.")
