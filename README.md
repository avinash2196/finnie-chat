# 🚀 Finnie Chat — Multi-Agent Financial AI Assistant

A **production-style, multi-agent AI system** designed to deliver **portfolio insights, financial education, and market analysis** through intelligent orchestration, RAG pipelines, and real-time data integrations.

Built with a focus on **scalability, observability, and modular AI architecture**, Finnie Chat demonstrates how modern AI systems can combine **LLMs, domain agents, and structured data systems** into a cohesive platform.

---

## 🧠 Why This Project Matters

Most AI chatbots are **single-agent and stateless**.  
Finnie Chat introduces a **multi-agent orchestration architecture** that:

- Routes user intent to **specialized financial agents**
- Combines **structured portfolio data + unstructured knowledge (RAG)**
- Ensures **safe, explainable, and domain-aware responses**
- Supports **multi-provider LLM fallback with reliability controls**

👉 This mirrors **real-world AI platform design** used in fintech and enterprise AI systems.

---

## 🏗️ Architecture Overview

![Architecture Diagram](docs/architecture.svg)

### Core Components

- **Orchestrator**
  - Central brain that routes requests to the right agent
  - Handles intent classification, fallback, and response aggregation

- **Domain Agents (Multi-Agent System)**
  - Portfolio Coach
  - Market Analyst
  - Risk Profiler
  - Financial Educator
  - Compliance & Safety Guard
  - Strategy & Screening Agent

- **AI Gateway**
  - Multi-LLM provider routing (OpenAI, Gemini, etc.)
  - Circuit breaker + fallback handling
  - TTL caching for performance optimization

- **RAG Pipeline**
  - Financial knowledge base using embeddings
  - Context-aware responses with “Don’t Know” fallback

- **Data Layer**
  - SQLAlchemy-backed portfolio system
  - Tracks holdings, transactions, and snapshots

- **Observability Layer**
  - LangSmith → tracing & debugging
  - Arize AI → model quality & safety monitoring

---

## ⚙️ Tech Stack

**Backend**
- FastAPI, Python
- SQLAlchemy (SQLite / PostgreSQL ready)
- Async architecture (Uvicorn)

**AI / ML**
- OpenAI / Gemini (multi-provider support)
- LangChain / orchestration layer
- RAG (vector-based retrieval)

**Frontend**
- Streamlit (interactive UI)

**Observability**
- LangSmith (tracing)
- Arize AI (evaluation & monitoring)

**Infra Ready**
- Docker support
- Redis (optional caching layer)
- Modular deployment-ready structure

---

## ✨ Key Features

### 🤖 Multi-Agent Orchestration
- Intent-driven routing to specialized agents
- Separation of concerns across financial domains

### 📊 Portfolio Intelligence
- Persistent portfolio tracking (holdings, transactions)
- Context-aware financial insights

### 📈 Market Analysis Integration
- Real-time data via market APIs
- Trend and signal interpretation

### 📚 Financial RAG System
- Domain-specific knowledge retrieval
- Reduces hallucination via grounded responses

### 🛡️ Safety & Guardrails
- Compliance-aware responses
- Fallback to safe outputs when uncertain

### 🔁 AI Gateway with Fallback
- Multi-provider LLM routing
- Circuit breaker for resilience
- Response caching

### 📡 Observability Built-In
- Full tracing of LLM calls
- Evaluation hooks for response quality

---

## 🚀 Quick Start

```bash
# Clone repo
git clone https://github.com/avinash2196/finnie-chat.git
cd finnie-chat

# Create virtual environment
python -m venv venv
source venv/bin/activate  # (Windows: venv\Scripts\activate)

# Install dependencies
pip install -r requirements.txt

# Start backend
uvicorn app.main:app --reload

# Start frontend (optional)
streamlit run frontend/app.py
```

---

## 🔌 Example API Usage

```bash
POST /chat

{
  "message": "Analyze my portfolio risk",
  "user_id": "user123"
}
```

### Sample Flow
1. User query received
2. Orchestrator detects intent → Risk Analysis
3. Risk Profiler Agent activated
4. Portfolio data + AI reasoning combined
5. Response returned with explanation

---

## 🧪 Testing & Quality

- Unit + integration test coverage across agents and APIs
- Designed for **deterministic + LLM-based evaluation**
- Hooks available for:
  - Prompt testing
  - Response validation
  - Observability-driven debugging

---

## 📊 System Design Highlights

- **Microservice-ready modular architecture**
- **Agent-based decomposition (scalable pattern)**
- **Separation of orchestration vs execution**
- **AI Gateway abstraction (provider-agnostic design)**
- **Extensible memory & context handling**

---

## 🔮 Roadmap

- [ ] Vector DB integration (FAISS / Chroma / Pinecone)
- [ ] Advanced portfolio analytics (Sharpe ratio, VaR)
- [ ] Real-time streaming market updates
- [ ] Kubernetes / Cloud Run deployment templates
- [ ] Auth layer (JWT-based user sessions)

---

## 👨‍💻 Author

**Avinash Srivastava**  
Senior Software Engineer | Distributed Systems | AI Platforms

- Expertise in building **scalable backend systems, AI pipelines, and cloud-native architectures**
- Focused on **multi-agent AI systems, RAG, and real-time data platforms**

---

## ⭐ Why This Stands Out

This project goes beyond a typical chatbot by demonstrating:

- Real-world **multi-agent system design**
- Integration of **AI + structured financial systems**
- Production-grade concerns: **resilience, observability, modularity**

👉 Designed as a **portfolio-grade system** reflecting modern AI platform engineering.
