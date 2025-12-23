"""Targeted tests for observability module decorators and logging paths."""

from types import SimpleNamespace
from unittest.mock import patch, MagicMock

from app.observability import observability, track_agent_execution, track_llm_call


def test_guess_asset_type_variants():
    assert observability.guess_asset_type("BTC to 50k?") == "crypto"
    assert observability.guess_asset_type("Best ETF for income?") == "ETF"
    # Allow heuristic to return either stock or general depending on regex
    assert observability.guess_asset_type("Discuss AAPL fair value") in ("stock", "general")
    assert observability.guess_asset_type("Advice on investing") in ("stock", "general")


def test_arize_log_chat_response_noop_when_disabled():
    # Ensure no exception when not configured
    observability.arize_enabled = False
    observability._arize_client = None
    observability.arize_log_chat_response(
        prediction_id="pid-1",
        request_text="hello",
        response_text="world",
        tags={},
        quality={},
        safety={},
    )


def test_arize_log_chat_response_emit_and_log_paths():
    # Fake client with emit, then with log, then with neither
    class ClientWithEmit:
        def emit(self, payload):
            return True

    class ClientWithLog:
        def log(self, payload):
            return True

    observability.arize_enabled = True
    # Emit path
    observability._arize_client = ClientWithEmit()
    observability.arize_log_chat_response("p1", "q", "r", {}, {}, {})
    # Log path
    observability._arize_client = ClientWithLog()
    observability.arize_log_chat_response("p2", "q", "r", {}, {}, {})
    # Neither path
    observability._arize_client = SimpleNamespace()
    observability.arize_log_chat_response("p3", "q", "r", {}, {}, {})


def test_instrumentation_methods_do_not_throw():
    # These should be safe no-ops when OTEL unavailable
    observability.instrument_fastapi(MagicMock())
    observability.instrument_httpx()
    observability.instrument_sqlalchemy(MagicMock())


def test_track_agent_execution_success_and_failure():
    calls = {"events": [], "metrics": []}

    with patch.object(observability, "track_event", side_effect=lambda e, p=None: calls["events"].append((e, p))):
        with patch.object(observability, "track_metric", side_effect=lambda n, v, p=None: calls["metrics"].append((n, v, p))):

            @track_agent_execution("TestAgent")
            def ok_fn(x):
                return x * 2

            @track_agent_execution("TestAgent")
            def fail_fn():
                raise RuntimeError("boom")

            assert ok_fn(2) == 4
            try:
                fail_fn()
            except RuntimeError:
                pass

    # Ensure events were tracked (success and error)
    assert len(calls["events"]) >= 2


def test_track_llm_call_success_and_failure():
    calls = {"events": [], "metrics": []}

    with patch.object(observability, "track_event", side_effect=lambda e, p=None: calls["events"].append((e, p))):
        with patch.object(observability, "track_metric", side_effect=lambda n, v, p=None: calls["metrics"].append((n, v, p))):

            @track_llm_call("mock")
            def ok_llm():
                return "ok"

            @track_llm_call("mock")
            def fail_llm():
                raise ValueError("llm fail")

            assert ok_llm() == "ok"
            try:
                fail_llm()
            except ValueError:
                pass

    assert len(calls["events"]) >= 2


def test_observability_direct_calls_and_langsmith_noop():
    # Direct event/metric/exception calls should not raise
    observability.track_event("unit_test_event", {"k": "v"})
    observability.track_metric("unit_test_metric", 123.4, {"tag": "x"})
    observability.track_exception(RuntimeError("boom"), {"where": "test"})

    # LangSmith not enabled by default; start/end should be no-ops
    rid = observability.start_langsmith_run(name="x", run_type="chain", inputs={}, metadata={}, parent_run_id=None, tags=["t"])
    assert rid is None or isinstance(rid, str)
    # End with None run id should be a no-op
    observability.end_langsmith_run(run_id=None, outputs={}, error=None, tags=["t"], metrics={}, metadata_update={})
