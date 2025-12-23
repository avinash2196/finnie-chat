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
    # simulate arize client having log that fails and emit available
    import app.observability as ob
    mgr = ObservabilityManager()

    class BadClient:
        def log(self, **kwargs):
            raise RuntimeError("log failed")
        def emit(self, payload):
            # mark called
            mgr._emit_called = True

    mgr.arize_enabled = True
    mgr._arize_client = BadClient()

    mgr.arize_log_chat_response(prediction_id="p", request_text="r", response_text="s", tags={}, quality={}, safety={})
    assert getattr(mgr, "_emit_called", False) is True


def test_instrumentation_attempts(monkeypatch):
    # force OTEL_AVAILABLE True and ensure instrument_* methods attempt calls
    import app.observability as ob
    monkeypatch.setattr(ob, "OTEL_AVAILABLE", True)

    class DummyInstr:
        @staticmethod
        def instrument_app(app):
            pass
    monkeypatch.setattr(ob, "FastAPIInstrumentor", DummyInstr)
    monkeypatch.setattr(ob, "HTTPXClientInstrumentor", DummyInstr)
    monkeypatch.setattr(ob, "SQLAlchemyInstrumentor", DummyInstr)

    mgr = ObservabilityManager()
    mgr.instrument_fastapi(object())
    mgr.instrument_httpx()
    mgr.instrument_sqlalchemy(object())
