"""
Tests for observability module.
"""
import pytest
from unittest.mock import patch, MagicMock
from app.observability import ObservabilityManager, track_agent_execution, track_llm_call


class TestObservabilityManager:
    """Test ObservabilityManager initialization and status."""
    
    def test_initialization_without_credentials(self):
        """Test that ObservabilityManager initializes even without credentials."""
        with patch.dict('os.environ', {}, clear=True):
            obs = ObservabilityManager()
            assert obs.langsmith_enabled == False
    
    def test_get_status(self):
        """Test get_status returns correct structure."""
        obs = ObservabilityManager()
        status = obs.get_status()
        
        assert "langsmith_available" in status
        assert "langsmith_enabled" in status
        assert "arize_enabled" in status
        assert "service_version" in status

    
    def test_langsmith_setup_with_api_key(self):
        """Test LangSmith setup with API key."""
        with patch.dict('os.environ', {
            'LANGSMITH_API_KEY': 'test_api_key',
            'LANGSMITH_PROJECT': 'test_project'
        }):
            with patch('app.observability.LangSmithClient'):
                obs = ObservabilityManager()
                assert obs.langsmith_api_key == 'test_api_key'
                assert obs.langsmith_project == 'test_project'


class TestTrackingDecorators:
    """Test tracking decorators."""
    
    def test_track_agent_execution_success(self):
        """Test agent execution tracking on success."""
        @track_agent_execution("TestAgent")
        def dummy_agent():
            return "success"
        
        result = dummy_agent()
        assert result == "success"
    
    def test_track_agent_execution_failure(self):
        """Test agent execution tracking on failure."""
        @track_agent_execution("TestAgent")
        def failing_agent():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError, match="Test error"):
            failing_agent()
    
    def test_track_llm_call_success(self):
        """Test LLM call tracking on success."""
        @track_llm_call("openai")
        def dummy_llm_call():
            return "LLM response"
        
        result = dummy_llm_call()
        assert result == "LLM response"
    
    def test_track_llm_call_failure(self):
        """Test LLM call tracking on failure."""
        @track_llm_call("openai")
        def failing_llm_call():
            raise RuntimeError("API timeout")
        
        with pytest.raises(RuntimeError, match="API timeout"):
            failing_llm_call()


class TestObservabilityIntegration:
    """Test observability integration methods."""
    
    def test_track_event(self):
        """Test track_event doesn't crash without Azure."""
        obs = ObservabilityManager()
        # Should not raise even if Azure not configured
        obs.track_event("test_event", {"key": "value"})
    
    def test_track_metric(self):
        """Test track_metric doesn't crash without Azure."""
        obs = ObservabilityManager()
        # Should not raise even if Azure not configured
        obs.track_metric("test_metric", 123.45, {"key": "value"})
    
    def test_track_exception(self):
        """Test track_exception doesn't crash without Azure."""
        obs = ObservabilityManager()
        try:
            raise ValueError("Test exception")
        except Exception as e:
            # Should not raise even if Azure not configured
            obs.track_exception(e, {"context": "test"})
    
    def test_instrument_fastapi(self):
        """Test FastAPI instrumentation returns None (no-op)."""
        obs = ObservabilityManager()
        mock_app = MagicMock()
        result = obs.instrument_fastapi(mock_app)
        assert result is None  # Safe no-op
    
    def test_instrument_httpx(self):
        """Test HTTPX instrumentation returns None (no-op)."""
        obs = ObservabilityManager()
        result = obs.instrument_httpx()
        assert result is None  # Safe no-op
    
    def test_instrument_sqlalchemy(self):
        """Test SQLAlchemy instrumentation returns None (no-op)."""
        obs = ObservabilityManager()
        mock_engine = MagicMock()
        result = obs.instrument_sqlalchemy(mock_engine)
        assert result is None  # Safe no-op


class TestObservabilityExtras:
    """Additional tests to increase coverage for observability module."""
    
    def test_arize_log_chat_response_noop_and_emit(self):
        obs = ObservabilityManager()
        # No-op path when disabled
        obs.arize_enabled = False
        obs._arize_client = None
        obs.arize_log_chat_response(
            prediction_id="p1",
            request_text="q",
            response_text="r",
            tags={}, quality={}, safety={}
        )
        
        # Enabled path with mock client
        class DummyClient:
            def emit(self, payload):
                pass
        obs.arize_enabled = True
        obs._arize_client = DummyClient()
        obs.arize_log_chat_response(
            prediction_id="p2",
            request_text="q2",
            response_text="r2",
            tags={"t":1}, quality={"q":1}, safety={"s":1}
        )


def test_guess_asset_type_variants():
    # Verify heuristics for common asset strings
    from app.observability import observability as _obs
    assert _obs.guess_asset_type("BTC") == "crypto"
    assert _obs.guess_asset_type("This mentions XLK ETF") == "etf"
    assert _obs.guess_asset_type("AAPL") == "stock"
    assert _obs.guess_asset_type("12345") == "general"


def test_decorators_emit_events_and_exceptions(monkeypatch):
    # Capture calls made by decorators when using the global observability instance
    from app.observability import observability as _obs, track_agent_execution, track_llm_call

    events = []
    metrics = []
    exceptions = []

    monkeypatch.setattr(_obs, "track_event", lambda *a, **k: events.append(a))
    monkeypatch.setattr(_obs, "track_metric", lambda *a, **k: metrics.append(a))
    monkeypatch.setattr(_obs, "track_exception", lambda *a, **k: exceptions.append(a))

    @track_agent_execution("XAgent")
    def good(x):
        return x + 1

    @track_agent_execution("XAgent")
    def bad(x):
        raise RuntimeError("fail")

    @track_llm_call("openai")
    def ok_llm(s):
        return s

    @track_llm_call("openai")
    def fail_llm(s):
        raise ValueError("boom")

    assert good(1) == 2
    with pytest.raises(RuntimeError):
        bad(1)

    assert ok_llm("x") == "x"
    with pytest.raises(ValueError):
        fail_llm("x")

    # Decorators emit metrics for successful calls and exceptions for failures
    assert len(metrics) >= 2  # At least 2 successful metric calls
    assert len(exceptions) >= 2  # At least 2 exception calls
