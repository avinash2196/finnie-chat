import os
import types
from app.observability import ObservabilityManager


def test_langsmith_setup_and_run_update(monkeypatch):
    # Ensure a fake LangSmith client path is exercised
    monkeypatch.setenv("LANGSMITH_API_KEY", "x")
    monkeypatch.setenv("LANGSMITH_PROJECT", "testproj")

    class FakeRun:
        def __init__(self):
            self.id = "run-1"
    class FakeLangSmithClient:
        def __init__(self, api_key=None):
            self.api_key = api_key
        def create_run(self, **kwargs):
            return FakeRun()
        def update_run(self, run_id, **kwargs):
            return True

    # Patch module-level LANGSMITH_AVAILABLE and LangSmithClient symbol
    import app.observability as ob
    monkeypatch.setattr(ob, "LANGSMITH_AVAILABLE", True)
    monkeypatch.setattr(ob, "LangSmithClient", FakeLangSmithClient)

    # Recreate manager to pick up patched client
    mgr = ObservabilityManager()
    run_id = mgr.start_langsmith_run(name="t", run_type="chain", inputs={})
    assert run_id == "run-1"
    mgr.end_langsmith_run(run_id, outputs={"o":1})


def test_arize_client_log_and_emit_fallback(monkeypatch):
    # Test that arize_log_chat_response handles exceptions gracefully
    import app.observability as ob
    mgr = ObservabilityManager()

    class BadClient:
        def log(self, **kwargs):
            raise RuntimeError("log failed")

    mgr.arize_enabled = True
    mgr._arize_client = BadClient()

    # Should not raise even if log fails
    mgr.arize_log_chat_response(prediction_id="p", request_text="r", response_text="s", tags={}, quality={}, safety={})
    assert mgr.arize_enabled is True  # Should still be enabled despite error

def test_instrumentation_attempts(monkeypatch):
    # Test that instrumentation methods are safe no-ops
    import app.observability as ob

    mgr = ObservabilityManager()
    
    # These should return None (no-op)
    assert mgr.instrument_fastapi(object()) is None
    assert mgr.instrument_httpx() is None
    assert mgr.instrument_sqlalchemy(object()) is None
