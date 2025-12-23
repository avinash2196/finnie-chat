"""
Observability & Monitoring Configuration
LangSmith tracing and Arize AI logging only.
"""
import os
import logging
from typing import Optional, Dict, Any
from functools import wraps
import time


# OpenTelemetry
try:
    from opentelemetry import trace, metrics
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_NAMESPACE, SERVICE_VERSION
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from opentelemetry.instrumentation.logging import LoggingInstrumentor
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    logging.warning("OpenTelemetry packages not installed")
    # Provide stubs so tests can patch these symbols even without OTEL installed
    class FastAPIInstrumentor:  # type: ignore
        @staticmethod
        def instrument_app(app):
            return None
    class HTTPXClientInstrumentor:  # type: ignore
        def instrument(self):
            return None
    class SQLAlchemyInstrumentor:  # type: ignore
        def instrument(self, engine=None):
            return None
    class LoggingInstrumentor:  # type: ignore
        def instrument(self):
            return None

# LangSmith
try:
    from langsmith import Client as LangSmithClient
    LANGSMITH_AVAILABLE = True
except ImportError:
    LANGSMITH_AVAILABLE = False
    logging.warning("LangSmith not installed")


logger = logging.getLogger(__name__)


class ObservabilityManager:
    """
    Centralized observability manager for LangSmith and Arize AI.
    """
    
    def __init__(self):
        self.langsmith_enabled = False
        self.telemetry_client: Optional[object] = None
        self.langsmith_client: Optional[LangSmithClient] = None
        self.tracer_provider: Optional[TracerProvider] = None
        self.meter_provider: Optional[MeterProvider] = None
        
        # LangSmith configuration
        self.langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
        self.langsmith_project = os.getenv("LANGSMITH_PROJECT", "finnie-chat")
        
        # Service configuration
        self.service_name = os.getenv("OTEL_SERVICE_NAME", "finnie-chat")
        self.service_namespace = "financial-ai"
        self.service_version = "1.0.0"
        
        self._setup_langsmith()
        self._setup_opentelemetry()

        # Arize AI configuration (optional)
        self.arize_enabled = False
        self._setup_arize()
    
    def _setup_langsmith(self):
        """Initialize LangSmith tracing."""
        if not LANGSMITH_AVAILABLE:
            logger.warning("LangSmith not available")
            return
        
        if self.langsmith_api_key:
            try:
                # Set environment variables for LangSmith
                os.environ["LANGCHAIN_TRACING_V2"] = "true"
                os.environ["LANGCHAIN_PROJECT"] = self.langsmith_project
                os.environ["LANGCHAIN_API_KEY"] = self.langsmith_api_key
                
                # Initialize LangSmith client
                self.langsmith_client = LangSmithClient(api_key=self.langsmith_api_key)
                
                self.langsmith_enabled = True
                logger.info(f"✅ LangSmith initialized (Project: {self.langsmith_project})")
                
            except Exception as e:
                logger.error(f"Failed to initialize LangSmith: {e}")
        else:
            logger.info("LangSmith not configured (missing API key)")

    # ---------------------------
    # LangSmith Run Helpers
    # ---------------------------
    def start_langsmith_run(
        self,
        name: str,
        run_type: str,
        inputs: Dict[str, Any] | None = None,
        metadata: Dict[str, Any] | None = None,
        parent_run_id: Optional[str] = None,
        tags: list[str] | None = None,
    ) -> Optional[str]:
        """Create a LangSmith run and return its id (no-op if unavailable)."""
        if not self.langsmith_enabled or not self.langsmith_client:
            return None
        try:
            run = self.langsmith_client.create_run(
                name=name,
                inputs=inputs or {},
                run_type=run_type,
                parent_run_id=parent_run_id,
                tags=tags or [],
                extra={"metadata": metadata or {}}
            )
            return getattr(run, "id", None)
        except Exception as e:
            logger.debug(f"LangSmith create_run failed: {e}")
            return None

    def end_langsmith_run(
        self,
        run_id: Optional[str],
        outputs: Dict[str, Any] | None = None,
        error: Optional[str] = None,
        tags: list[str] | None = None,
        metrics: Dict[str, Any] | None = None,
        metadata_update: Dict[str, Any] | None = None,
    ) -> None:
        """End/update a LangSmith run (no-op if unavailable)."""
        if not run_id or not self.langsmith_enabled or not self.langsmith_client:
            return
        try:
            self.langsmith_client.update_run(
                run_id=run_id,
                outputs=outputs or {},
                error=error,
                tags=tags,
                extra={
                    "metadata": metadata_update or {},
                    "metrics": metrics or {},
                }
            )
        except Exception as e:
            logger.debug(f"LangSmith update_run failed: {e}")
    
    def _setup_opentelemetry(self):
        """Initialize OpenTelemetry tracing (optional)."""
        # OpenTelemetry optional; no exporters configured
        return

    # ---------------------------
    # Arize AI (optional)
    # ---------------------------
    def _setup_arize(self):
        """Initialize Arize client if available and configured."""
        self.arize_api_key = os.getenv("ARIZE_API_KEY")
        self.arize_space_key = os.getenv("ARIZE_SPACE_KEY")
        self.arize_org_key = os.getenv("ARIZE_ORG_KEY")
        self.arize_model_id = os.getenv("ARIZE_MODEL_ID", "finnie-chat")
        self.arize_model_version = os.getenv("ARIZE_MODEL_VERSION", self.service_version)
        try:
            # Lazy import to avoid hard dependency
            from arize.api import Client as ArizeClient  # type: ignore
            self._ArizeClient = ArizeClient  # store class
            if self.arize_api_key and self.arize_space_key:
                client_kwargs = {
                    "space_key": self.arize_space_key,
                    "api_key": self.arize_api_key,
                }
                try:
                    # Older Arize SDK versions do not accept organization_key
                    if self.arize_org_key:
                        self._arize_client = ArizeClient(
                            **client_kwargs,
                            organization_key=self.arize_org_key,
                        )
                    else:
                        self._arize_client = ArizeClient(**client_kwargs)
                except TypeError:
                    # Fallback for SDKs that exclude organization_key
                    self._arize_client = ArizeClient(**client_kwargs)
                self.arize_enabled = True
                logger.info("✅ Arize AI client configured")
            else:
                self._arize_client = None
                logger.info("Arize AI not configured (set ARIZE_* env vars to enable)")
        except Exception as e:  # ImportError or runtime errors
            self._ArizeClient = None
            self._arize_client = None
            logger.info(f"Arize AI SDK not available: {e}")
    
    def instrument_fastapi(self, app):
        """Instrument FastAPI app with observability."""
        # Keep method for API parity; do nothing if OTEL not present
        if OTEL_AVAILABLE:
            try:
                FastAPIInstrumentor.instrument_app(app)
                logger.info("✅ FastAPI instrumented (OTEL)")
            except Exception as e:
                logger.debug(f"FastAPI instrumentation skipped: {e}")
    
    def instrument_httpx(self):
        """Instrument HTTPX client."""
        if OTEL_AVAILABLE:
            try:
                HTTPXClientInstrumentor().instrument()
                logger.info("✅ HTTPX instrumented (OTEL)")
            except Exception as e:
                logger.debug(f"HTTPX instrumentation skipped: {e}")
    
    def instrument_sqlalchemy(self, engine):
        """Instrument SQLAlchemy engine."""
        if OTEL_AVAILABLE:
            try:
                SQLAlchemyInstrumentor().instrument(engine=engine)
                logger.info("✅ SQLAlchemy instrumented (OTEL)")
            except Exception as e:
                logger.debug(f"SQLAlchemy instrumentation skipped: {e}")
    
    def track_event(self, event_name: str, properties: dict = None):
        """Track custom event (debug log)."""
        logger.debug(f"event: {event_name} props={properties or {}}")
    
    def track_metric(self, metric_name: str, value: float, properties: dict = None):
        """Track custom metric (debug log)."""
        logger.debug(f"metric: {metric_name} value={value} props={properties or {}}")
    
    def track_exception(self, exception: Exception, properties: dict = None):
        """Track exception (debug log)."""
        logger.debug(f"exception: {type(exception).__name__} props={properties or {}}")
    
    def get_status(self) -> dict:
        """Get observability status."""
        return {
            "langsmith_available": LANGSMITH_AVAILABLE,
            "langsmith_enabled": self.langsmith_enabled,
            "langsmith_project": self.langsmith_project if self.langsmith_enabled else None,
            "opentelemetry_available": OTEL_AVAILABLE,
            "service_name": self.service_name,
            "service_namespace": self.service_namespace,
            "cloud_provider": "local",
            "cloud_region": "local",
            "arize_enabled": self.arize_enabled,
            "arize_model_id": self.arize_model_id if self.arize_enabled else None,
            "arize_model_version": self.arize_model_version if self.arize_enabled else None,
        }

    # ---------------------------
    # Utility helpers
    # ---------------------------
    @staticmethod
    def guess_asset_type(text: str) -> str:
        t = (text or "").upper()
        if any(k in t for k in ["BTC", "ETH", "CRYPTO"]):
            return "crypto"
        if "ETF" in t:
            return "ETF"
        # crude ticker heuristic: 1-5 uppercase letters/dots
        import re
        if re.search(r"\b[A-Z]{1,5}(\.[A-Z]{1,2})?\b", t):
            return "stock"
        return "general"

    # ---------------------------
    # Arize logging facade (safe no-op if disabled)
    # ---------------------------
    def arize_log_chat_response(
        self,
        prediction_id: str,
        request_text: str,
        response_text: str,
        tags: Dict[str, Any],
        quality: Dict[str, Any],
        safety: Dict[str, Any],
    ) -> None:
        """Log a chat response to Arize AI (no-op if not configured)."""
        if not self.arize_enabled or not getattr(self, "_arize_client", None):
            logger.debug("Arize not enabled; skipping log")
            return
        try:
            # Best-effort generic logging to Arize; exact schema varies by SDK version
            # We send a single prediction-like event with rich metadata
            payload = {
                "prediction_id": prediction_id,
                "model_id": self.arize_model_id,
                "model_version": self.arize_model_version,
                "prediction_label": "finance_advice_explanation",
                "features": {
                    "request_text": request_text,
                    "response_text": response_text,
                },
                "tags": tags | quality | safety,
            }
            logger.debug(
                "Arize emit payload",
                extra={
                    "prediction_id": prediction_id,
                    "model_id": self.arize_model_id,
                    "model_version": self.arize_model_version,
                    "has_emit": hasattr(self._arize_client, "emit"),
                    "has_log": hasattr(self._arize_client, "log"),
                },
            )
            # Use generic client.emit if available, else try .log
            client = self._arize_client
            if hasattr(client, "log"):
                try:
                    from arize.utils.types import ModelTypes, Environments

                    client.log(  # type: ignore[attr-defined]
                        model_id=self.arize_model_id,
                        model_version=self.arize_model_version,
                        model_type=ModelTypes.GENERATIVE_LLM,
                        environment=Environments.PRODUCTION,
                        prediction_id=prediction_id,
                        prediction_label="finance_advice_explanation",
                        tags=tags | quality | safety,
                        features={
                            "request_text": request_text,
                            "response_text": response_text,
                        },
                    )
                    return
                except Exception as log_err:
                    logger.debug(f"Arize log failed; will try emit fallback: {log_err}")
            if hasattr(client, "emit"):
                client.emit(payload)  # type: ignore[attr-defined]
            else:
                logger.debug("Arize client has no emit/log; skipping")
        except Exception as e:
            logger.debug(f"Arize logging failed: {e}")


# Global instance
observability = ObservabilityManager()


def track_agent_execution(agent_name: str):
    """
    Decorator to track agent execution time and results.
    
    Usage:
        @track_agent_execution("MarketAgent")
        def run_market_agent(message):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Track success
                observability.track_event(
                    f"{agent_name}_execution",
                    {
                        "agent": agent_name,
                        "duration_ms": duration * 1000,
                        "status": "success"
                    }
                )
                observability.track_metric(f"{agent_name}_duration", duration * 1000)
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                # Track failure
                observability.track_event(
                    f"{agent_name}_execution",
                    {
                        "agent": agent_name,
                        "duration_ms": duration * 1000,
                        "status": "error",
                        "error": str(e)
                    }
                )
                observability.track_exception(e, {"agent": agent_name})
                
                raise
        
        return wrapper
    return decorator


def track_llm_call(provider: str):
    """
    Decorator to track LLM API calls.
    
    Usage:
        @track_llm_call("openai")
        def call_openai(prompt):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Track success
                observability.track_event(
                    "llm_call",
                    {
                        "provider": provider,
                        "duration_ms": duration * 1000,
                        "status": "success"
                    }
                )
                observability.track_metric(f"llm_{provider}_duration", duration * 1000)
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                # Track failure
                observability.track_event(
                    "llm_call",
                    {
                        "provider": provider,
                        "duration_ms": duration * 1000,
                        "status": "error",
                        "error": str(e)
                    }
                )
                observability.track_exception(e, {"provider": provider})
                
                raise
        
        return wrapper
    return decorator
