"""
Observability & Monitoring Configuration

FINAL VERSION
- LangSmith runs never hang
- Fully backward compatible with existing code
- Safe no-ops for optional integrations
"""

import os
import time
import logging
from typing import Optional, Dict, Any
from functools import wraps

logger = logging.getLogger(__name__)

# -------------------------------------------------
# LangSmith
# -------------------------------------------------
try:
    from langsmith import Client as LangSmithClient
    LANGSMITH_AVAILABLE = True
except ImportError:
    LANGSMITH_AVAILABLE = False


class ObservabilityManager:
    """
    Centralized observability manager.
    """

    def __init__(self):
        # ---- Service metadata (compatibility) ----
        self.service_version = os.getenv("SERVICE_VERSION", "1.0.0")

        # ---- LangSmith config ----
        self.langsmith_enabled = False
        self.langsmith_client: Optional[LangSmithClient] = None
        self.langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
        self.langsmith_project = os.getenv("LANGSMITH_PROJECT", "finnie-chat")

        # ---- Arize config (optional) ----
        self.arize_enabled = False

        self._setup_langsmith()
        self._setup_arize()

    # -------------------------------------------------
    # LangSmith setup
    # -------------------------------------------------
    def _setup_langsmith(self):
        if not LANGSMITH_AVAILABLE:
            logger.info("LangSmith SDK not installed")
            return

        if not self.langsmith_api_key:
            logger.info("LangSmith not configured (missing API key)")
            return

        try:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_PROJECT"] = self.langsmith_project
            os.environ["LANGCHAIN_API_KEY"] = self.langsmith_api_key

            self.langsmith_client = LangSmithClient(
                api_key=self.langsmith_api_key
            )
            self.langsmith_enabled = True
            logger.info(f"✅ LangSmith initialized (project={self.langsmith_project})")
        except Exception as e:
            logger.error(f"LangSmith initialization failed: {e}")

    # -------------------------------------------------
    # LangSmith run lifecycle (SYNC & GUARANTEED)
    # -------------------------------------------------
    def start_langsmith_run(
        self,
        name: str,
        run_type: str,
        inputs: Dict[str, Any] | None = None,
        metadata: Dict[str, Any] | None = None,
        parent_run_id: Optional[str] = None,
        tags: list[str] | None = None,
    ) -> Optional[str]:
        if not self.langsmith_enabled or not self.langsmith_client:
            return None

        try:
            run = self.langsmith_client.create_run(
                name=name,
                run_type=run_type,
                inputs=inputs or {},
                parent_run_id=parent_run_id,
                tags=tags or [],
                extra={"metadata": metadata or {}},
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
                },
            )
        except Exception as e:
            logger.debug(f"LangSmith update_run failed: {e}")

    # -------------------------------------------------
    # Arize AI (optional, safe no-op)
    # -------------------------------------------------
    def _setup_arize(self):
        self.arize_api_key = os.getenv("ARIZE_API_KEY")
        self.arize_space_key = os.getenv("ARIZE_SPACE_KEY")
        self.arize_org_key = os.getenv("ARIZE_ORG_KEY")
        self.arize_model_id = os.getenv("ARIZE_MODEL_ID", "finnie-chat")
        self.arize_model_version = os.getenv("ARIZE_MODEL_VERSION", self.service_version)

        try:
            from arize.api import Client as ArizeClient  # type: ignore
            if self.arize_api_key and self.arize_space_key:
                kwargs = {
                    "space_key": self.arize_space_key,
                    "api_key": self.arize_api_key,
                }
                if self.arize_org_key:
                    kwargs["organization_key"] = self.arize_org_key

                self._arize_client = ArizeClient(**kwargs)
                self.arize_enabled = True
                logger.info("✅ Arize AI configured")
            else:
                self._arize_client = None
        except Exception:
            self._arize_client = None

    def arize_log_chat_response(
        self,
        prediction_id: str,
        request_text: str,
        response_text: str,
        tags: Dict[str, Any],
        quality: Dict[str, Any],
        safety: Dict[str, Any],
    ) -> None:
        if not self.arize_enabled or not self._arize_client:
            return

        try:
            from arize.utils.types import ModelTypes, Environments
            self._arize_client.log(
                model_id=self.arize_model_id,
                model_version=self.arize_model_version,
                model_type=ModelTypes.GENERATIVE_LLM,
                environment=Environments.PRODUCTION,
                prediction_id=prediction_id,
                prediction_label="finance_response",
                tags=tags | quality | safety,
                features={
                    "request_text": request_text,
                    "response_text": response_text,
                },
            )
        except Exception as e:
            logger.debug(f"Arize log failed: {e}")

    # -------------------------------------------------
    # Compatibility stubs (NO-OP)
    # -------------------------------------------------
    def instrument_fastapi(self, app):
        return None

    def instrument_httpx(self):
        return None

    def instrument_sqlalchemy(self, engine):
        return None

    def get_status(self) -> dict:
        return {
            "langsmith_available": LANGSMITH_AVAILABLE,
            "langsmith_enabled": self.langsmith_enabled,
            "langsmith_project": self.langsmith_project if self.langsmith_enabled else None,
            "arize_enabled": self.arize_enabled,
            "service_version": self.service_version,
        }

    # -------------------------------------------------
    # Utility helpers (REQUIRED by main.py)
    # -------------------------------------------------
    def guess_asset_type(self, text: str) -> str:
        t = (text or "").upper()

        if any(k in t for k in ["BTC", "ETH", "CRYPTO", "BITCOIN", "ETHEREUM"]):
            return "crypto"

        if "ETF" in t:
            return "etf"

        # crude stock ticker heuristic
        import re
        if re.search(r"\b[A-Z]{1,5}(\.[A-Z]{1,2})?\b", t):
            return "stock"

        return "general"

    # -------------------------------------------------
    # Lightweight logging helpers
    # -------------------------------------------------
    def track_event(self, name: str, props: dict | None = None):
        logger.debug(f"event={name} props={props or {}}")

    def track_metric(self, name: str, value: float, props: dict | None = None):
        logger.debug(f"metric={name} value={value} props={props or {}}")

    def track_exception(self, exc: Exception, props: dict | None = None):
        logger.debug(f"exception={type(exc).__name__} props={props or {}}")


# -------------------------------------------------
# Global singleton
# -------------------------------------------------
observability = ObservabilityManager()


# -------------------------------------------------
# Decorators
# -------------------------------------------------
def track_agent_execution(agent_name: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                observability.track_metric(
                    f"{agent_name}_duration_ms",
                    (time.time() - start) * 1000,
                )
                return result
            except Exception as e:
                observability.track_exception(e, {"agent": agent_name})
                raise
        return wrapper
    return decorator


def track_llm_call(provider: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                observability.track_metric(
                    f"llm_{provider}_duration_ms",
                    (time.time() - start) * 1000,
                )
                return result
            except Exception as e:
                observability.track_exception(e, {"provider": provider})
                raise
        return wrapper
    return decorator
