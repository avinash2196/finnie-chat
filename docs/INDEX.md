# Finnie-Chat: Documentation Index

## Current Project Status

| Area | State |
|------|-------|
| Backend (FastAPI) | ✅ Complete |
| 9 Specialized Agents | ✅ Complete |
| Multi-provider LLM Gateway | ✅ Complete |
| SQLAlchemy DB + Portfolio Sync | ✅ Complete |
| Streamlit Frontend (4 pages) | ✅ Complete |
| RAG Engine (TF-IDF + sentence-transformers) | ✅ Complete |
| Observability (LangSmith, Arize) | ✅ Complete |
| Test suite | ✅ 452 passed, 1 known failure |
| Portfolio MCP → database | ⚠️ DB-backed variant built; not yet wired to agents |
| Alembic migrations | ⚠️ Dependency present; files not yet configured |

---

## 🏗️ Architecture

| Document | Purpose |
|----------|---------|
| [architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md) | Full system design, data flow, all 9 agents |
| [architecture/DATABASE_GUIDE.md](architecture/DATABASE_GUIDE.md) | Database models, provider pattern, REST API |
| [architecture/GATEWAY.md](architecture/GATEWAY.md) | Multi-provider LLM gateway, circuit breaker, caching |
| [architecture/OBSERVABILITY.md](architecture/OBSERVABILITY.md) | LangSmith + Arize tracing setup |

---

## 🚀 Getting Started

| Document | Purpose |
|----------|---------|
| [implementation/QUICK_START.md](implementation/QUICK_START.md) | Fastest path to running locally |
| [implementation/IMPLEMENTATION_GUIDE.md](implementation/IMPLEMENTATION_GUIDE.md) | Code reference, component descriptions, setup |

---

## 🧪 Testing

| Document | Purpose |
|----------|---------|
| [testing/TEST_COVERAGE.md](testing/TEST_COVERAGE.md) | Module-by-module test breakdown |
| [testing/TEST_IMPLEMENTATION_SUMMARY.md](testing/TEST_IMPLEMENTATION_SUMMARY.md) | Run commands, fixtures, CI guidance |

---

## 📊 Summaries

| Document | Purpose |
|----------|---------|
| [summaries/EXECUTIVE_SUMMARY.md](summaries/EXECUTIVE_SUMMARY.md) | What was delivered; open items |
| [summaries/FEATURE_COMPLETION_SUMMARY.md](summaries/FEATURE_COMPLETION_SUMMARY.md) | Feature completion details |
| [summaries/DATABASE_IMPLEMENTATION_SUMMARY.md](summaries/DATABASE_IMPLEMENTATION_SUMMARY.md) | Database layer implementation details |
| [summaries/DELIVERY_SUMMARY.md](summaries/DELIVERY_SUMMARY.md) | December 2025 sprint delivery |
| [UPDATES.md](UPDATES.md) | Detailed changelog with before/after comparisons |

---

## 📝 Planning Archive

The documents below are **historical planning artifacts**. Status fields in these files reflect the codebase at time of writing; they do not describe the current implementation.

| Document | Notes |
|----------|-------|
| [planning/REQUIREMENTS_ANALYSIS.md](planning/REQUIREMENTS_ANALYSIS.md) | Pre-sprint requirements; most gaps now resolved |
| [implementation/ROADMAP.md](implementation/ROADMAP.md) | Build roadmap; retained as history |
| [summaries/ANALYSIS_COMPLETE.md](summaries/ANALYSIS_COMPLETE.md) | Early-phase analysis; archived |
| [planning/DELIVERABLES.md](planning/DELIVERABLES.md) | Original deliverables list |
| [planning/high-architecture.md](planning/high-architecture.md) | Early high-level design sketch |

---

## 🌐 API Reference

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI spec: [external_portfolio_api.yaml](external_portfolio_api.yaml)

**"How do I run tests?"**
→ See `README.md` "Testing" section or `IMPLEMENTATION_GUIDE.md` "Key Commands"

**"What should I work on next?"**
→ See `ROADMAP.md` for current phase or `IMPLEMENTATION_GUIDE.md` for specific code

---

## ✅ Local Setup Checklist

- [ ] Python 3.11+ installed
- [ ] `pip install -r requirements.txt` completed
- [ ] `.env` created with at least `OPENAI_API_KEY`
- [ ] Backend starts: `uvicorn app.main:app --port 8000`
- [ ] Frontend starts: `streamlit run frontend/Home.py`

---

## 🧪 Testing Quick Reference

Run the full suite locally (no live API keys required):

```bash
pytest tests/ -v
# See test_results_full.txt in repo root for last recorded run
```

Run LLM-evaluation tests (requires live keys):
```bash
pytest tests/deepeval/ -v
```

See [testing/TEST_COVERAGE.md](testing/TEST_COVERAGE.md) for a module-by-module breakdown and [testing/TEST_IMPLEMENTATION_SUMMARY.md](testing/TEST_IMPLEMENTATION_SUMMARY.md) for fixture and run-command details.
