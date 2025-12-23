# Quick Setup: Observability (Arize + LangSmith)

## 🚀 5-Minute Setup

### 1. Install Dependencies
```bash
cd C:\Users\avina\Codes\finnie-chat
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment (Optional)

Edit `.env` with your keys:

```bash
# Arize AI (prediction logging + quality/safety)
ARIZE_API_KEY=your-arize-api-key
ARIZE_SPACE_KEY=your-arize-space-key
ARIZE_ORG_KEY=optional-org-key
ARIZE_MODEL_ID=finnie-chat
ARIZE_MODEL_VERSION=1.0.0

# LangSmith (LLM tracing)
LANGSMITH_API_KEY=lsv2_pt_your-key-here
LANGSMITH_PROJECT=finnie-chat
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com

# Optional tagging
PROMPT_VERSION=v1
AGENT_VERSION=1.0.0
```

**Get Arize Keys:** From your Arize workspace → API Settings.

**Get LangSmith Key:** https://smith.langchain.com → Settings → API Keys.

### 3. Start the App
```bash
.\start.bat
```

### 4. Verify Observability
```bash
# Check status
curl http://localhost:8000/observability/status

# Or visit in browser
http://localhost:8000/docs
```

**Expected Response (example):**
```json
{
  "status": {
    "langsmith_available": true,
    "langsmith_enabled": true,
    "langsmith_project": "finnie-chat",
    "arize_enabled": true
  },
  "message": "Observability services configured"
}
```

## ✅ What's Tracked Automatically

**Without any configuration:**
- ✅ Basic logging (console output)
- ✅ API endpoints accessible

**With LangSmith configured:**
- ✅ Complete LLM call traces (hierarchical runs)
- ✅ Token usage and latency
- ✅ Multi-agent orchestration flow

**With Arize configured:**
- ✅ Prediction logs with tags: prediction_type, model_version, prompt_version, agent_type, asset_type, compliance_category
- ✅ Quality signals: groundedness_score, retrieval_relevance, hallucination_risk, confidence_level
- ✅ Safety signals: pii_detected, restricted_advice_triggered, refusal_reason

## 📊 View Your Data

### Arize AI
- Arize → Models → Your space → View events, quality, and safety signals

### LangSmith
1. Go to https://smith.langchain.com/projects
2. Select `finnie-chat` project
3. View traces, latency, token usage

## 🧪 Test It

```bash
# Run observability tests
pytest tests/test_observability.py -v

# All tests pass even without credentials configured
```

## 🚫 Running Without Observability

**Don't want to set it up?** No problem!

- App works perfectly without Arize/LangSmith
- Observability is optional for local development
- All tracking is silent no-ops if not configured
- No performance impact

## 📚 Full Documentation

See [architecture/OBSERVABILITY.md](../architecture/OBSERVABILITY.md) for the complete guide.

## 🆘 Troubleshooting

**LangSmith not available**
```bash
pip install langsmith
```

**Arize SDK not installed**
```bash
pip install arize==7.8.0
```

**No data in dashboards**
- Wait 1-5 minutes for data to appear
- Check network connectivity
- Verify API keys are correct

**Import errors**
```bash
pip install -r requirements.txt --upgrade
```
