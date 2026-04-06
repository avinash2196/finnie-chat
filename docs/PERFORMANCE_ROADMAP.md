# Performance Roadmap (Hotspot Fixes)

Goal: Eliminate request latency caused by sequential external calls (yFinance, LLM providers) and reduce `/market/quote` p95 to <800ms for common requests.

Phases (prioritized):

- **Immediate (0-3 days)** — Reduce wall-clock I/O and add quick wins
  - Task: Add short-TTL (3-10s) in-memory cache for quote aggregation in `app/mcp/market.py` and `app/main.py`.
    - Owner: Backend
    - Effort: 1 day
    - Acceptance: `/market/quote` repeated requests for same tickers show >30% cache hit and median latency drop ≥25%.
  - Task: Add batching in the MCP server so multiple tickers are fetched in a single yfinance call where possible.
    - Owner: Backend (MCP)
    - Effort: 1-2 days
    - Acceptance: Per-symbol yfinance calls reduced; logs show fewer yfinance starts.

- **Short-term (3-10 days)** — Parallelize blocking I/O
  - Task: Run per-ticker yfinance fetches in a `ThreadPoolExecutor` (bounded pool) to make external calls concurrent.
    - Owner: Backend
    - Effort: 2 days
    - Acceptance: p95 latency drops significantly when many tickers requested; CPU usage within acceptable limits.
  - Task: Replace synchronous blocking client code in critical paths with non-blocking scheduling (use `anyio`/`asyncio.to_thread` or `starlette.concurrency.run_in_threadpool`).
    - Owner: Backend
    - Effort: 2-4 days
    - Acceptance: No regressions in tests; reduced request latency under load.

- **Medium-term (2-4 weeks)** — Architectural improvements and reliable caching
  - Task: Introduce Redis cache (short TTL indexing by symbol set) and metrics for cache hit/miss.
    - Owner: Backend / DevOps
    - Effort: 3-5 days (incl. infra + tests)
    - Acceptance: Cache hit rate > 40% for repeated traffic patterns; metric exported.
  - Task: Evaluate batched/paid market data API (one request for many tickers) or use a batched provider SDK instead of `yfinance` for hot paths.
    - Owner: Product/Backend
    - Effort: 3-7 days (PO + implementation)
    - Acceptance: Fewer outbound requests, predictable SLAs.

- **Long-term (4-8 weeks)** — Robust scaling and monitoring
  - Task: Move heavy aggregation to background workers (e.g., Celery, RQ, or a simple scheduler) to precompute movers/sectors.
  - Task: Add full tracing (OTel) + Grafana dashboards for `http_request_duration_ms`, `market_yfinance_call_ms`, and LLM call latencies. (currently not active)
  - Task: Define SLOs (p95 < 800ms for single-quote requests) and alerting on regressions.

Quick Wins Summary:
- Add in-process short-TTL cache for quotes (fastest impact)
- Batch yfinance calls and/or use a threadpool to parallelize
- Run a native profiler (py-spy) against a real `uvicorn` process to produce a flamegraph for deeper hotspots

How we'll validate fixes:
- Automated benchmark: simple runner that hits `/market/quote` with representative symbols and measures p50/p95 before/after change.
- Re-run the test suite and ensure no regression.
- Produce a flamegraph (`profile.svg`) to confirm reduction of blocking time in yfinance or thread waits.

Rollout plan:
- Apply change behind a feature flag or small rollout (dev/staging → canary → prod)
- Monitor metrics for 24-72 hours after rollout

Related files:
- `app/mcp/market.py` — MCP client cache
- `app/mcp/market_server.py` — yFinance server code (batching/parallelization)
- `app/main.py` — middleware/observability hooks

---

### Progress Update (implemented)

### Status Assessment (2025-12-23)

- Quick verification: backend is reachable and `/market/quote` returns expected shapes; short-TTL aggregation caching is active (observed fast cache hit on repeated request).
- Benchmarks: HTTP benchmark results saved (`benchmark_market_quote_http_results.json`) show large improvement (example p95 for 3-symbol requests reduced from ~1831ms to ~31ms). Smoke-test run showed a first-request time ≈0.866s and immediate cached repeat ≈0.016s.
- Frontend: `frontend/pages/2_📈_Market.py` was updated to use `st.cache_data` (ttl=5s) and an input debounce flow. The Streamlit process can be started and serves at `http://localhost:8501`, but UI verification requires interactive QA (some scripted GETs were intermittent during smoke runs). 
- Profiling: native profiler attempts (`py-spy`) were attempted but advisable to re-run under a controlled invocation (`py-spy record -- python -m uvicorn app.main:app`) to produce a reliable flamegraph.

### Testing & Coverage (2025-12-26)
- Test suite: Latest full test run — 452 passed, 1 failed (`tests/test_rag.py::test_rag_grounded_answer`)
- Observability: LangSmith enabled when configured; OTEL deferred; `instrument_*` are no-ops

### Is this production-grade?

Short answer: not yet.

Rationale:
- The core performance bottlenecks (sequential yfinance calls) have been addressed with batching, parallelization and short-TTL caching — verified by benchmarks.
- However, production readiness requires operational hardening, test automation, and observability before rolling to prod. Key gaps:
  - Redis-backed cache deployment and metrics for cache hit/miss (to avoid single-process cache limits and expose hit rates).
  - Full CI-run integration benchmarks and E2E UI tests (to prevent regressions and validate UI debounce across browsers).
  - Controlled canary/feature-flag rollout and monitoring (SLOs, alerts) to detect regressions under real traffic.
  - Security and dependency review, and a reproducible perf capture (py-spy flamegraph) run in staging.

### Action items required before production rollout

Deferred items (not yet implemented):
- Redis-backed cache with hit/miss metrics
- CI integration benchmark job
- py-spy flamegraph on staging
- OTel tracing and Grafana dashboards
- E2E frontend performance tests
- Canary rollout with SLO alerting

### What was implemented

- Short-TTL in-memory cache and `get_quotes` batch method in `app/mcp/market.py`.
- Batched MCP tool `get_quotes` and parallel per-ticker processing with retry/backoff in `app/mcp/market_server.py`.
- Short-lived aggregation cache with Redis support (fallback to in-memory) in `app/main.py` for `/market/quote`.

### Recent Results

- Live HTTP benchmark results are saved in `benchmark_market_quote_http_results.json`.
- Observed improvement: p95 for 3-symbol requests reduced from ~1831 ms (sequential baseline) to ~31 ms after batching, parallelization, and caching -- approximately 98% reduction.
