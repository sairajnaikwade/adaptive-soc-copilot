# Adaptive SOC CoPilot 🛡️
> **AI-Powered Security Operations Platform for Intelligent Threat Detection & Automated Response**

Adaptive SOC CoPilot is an enterprise-ready Security Operations Center (SOC) platform. It monitors user behavior, detects insider threats and compromised accounts using machine learning, explains all predictions via SHAP (Explainable AI), and executes automated response actions (such as triggering MFA or redirecting attackers to honeypots).

---

## 🏛️ System Architecture

```text
                    ┌─────────────────────────┐
                    │   Data Sources           │
                    │ (login logs, activity)   │
                    └───────────┬─────────────┘
                                ↓
                    ┌─────────────────────────┐
                    │  Event Ingestion API     │  ← single normalized
                    │  (FastAPI + Pydantic)    │    event schema
                    └───────────┬─────────────┘
                     ┌──────────┴──────────┐
                     ↓                     ↓
         ┌───────────────────┐  ┌───────────────────────┐
         │ Auth Monitoring   │  │ User Activity Monitor │
         │ (login rate, geo) │  │ (downloads, privs)    │
         └───────────┬───────┘  └───────────┬───────────┘
                     └──────────┬───────────┘
                                ↓
                    ┌─────────────────────────┐
                    │  Feature Extraction     │  ← sliding time windows
                    │  & Aggregation Window   │    (1h, 24h, 7d)
                    └───────────┬─────────────┘
                                ↓
                    ┌─────────────────────────┐
                    │  ML Anomaly Detection   │  ← Isolation Forest
                    │  (Score: -1.0 to 0.0)   │    (primary model)
                    └───────────┬─────────────┘
                                ↓
                    ┌─────────────────────────┐
                    │  SHAP Explanation       │  ← per-feature impact
                    │  Engine                 │    (positive/negative)
                    └───────────┬─────────────┘
                                ↓
                    ┌─────────────────────────┐
                    │  Trust Score &          │  ← Trust = max(0, 100 - penalities)
                    │  Confidence Engine      │    Confidence = f(anomaly_score, SHAP)
                    └───────────┬─────────────┘
                                ↓
                    ┌─────────────────────────┐
                    │  Rule Engine            │  ← Trust < 30 → High Risk
                    │  (Risk Classification)  │    Trust < 60 → Medium Risk
                    └───────────┬─────────────┘
                                ↓
                    ┌─────────────────────────┐
                    │  Adaptive Response      │  ← Low: Monitor
                    │  Engine                 │    Med: Alert + MFA
                    └───────────┬─────────────┘    High: Block / Honeypot
                                ↓
                    ┌─────────────────────────┐
                    │  SOC Copilot Dashboard  │  ← Threat Feed, SHAP Visuals,
                    │  (React 19 + Redux)     │    Response Overrides
                    └─────────────────────────┘
```

For the complete technical specification, normalized PostgreSQL schema, and mathematical definitions (Trust Score formulas, SHAP calculations), refer to [`SOC_CoPilot_System_Architecture.md`](file:///c:/Users/DELL5300%202IN%20-1/Desktop/adaptive-soc-copilot/SOC_CoPilot_System_Architecture.md).

---

## 🏗️ Clean Architecture & Core Features

- **Multi-Tenant Architecture**: Strict tenant isolation across all entities using PostgreSQL composite indexes.
- **Backend-First Design**: Modular Clean Architecture (`API → Services → Repositories → Database`).
- **Normalized Data Schema**: 17 normalized SQL tables tracking user activity, behavioral features, ML models, SHAP values, risk rules, and automated response actions.
- **Explainable AI (XAI)**: SHAP value storage mapped per feature for auditability and visual trust scores.
- **Automated Response Engine**: Configurable rule engine triggering proactive mitigation (MFA, account restriction, honeypot sessions).
- **Modern Security Dashboard**: React 19 + Redux Toolkit + Tailwind CSS dark-mode cyber interface.

---

## 🚀 Quick Start with Docker Compose

### Prerequisites
- Docker Engine `v24+` & Docker Compose `v2+`
- Python `3.11+` (for local development outside containers)
- Node.js `v20+` (for local frontend development)

### 1. Start Services via Docker Compose

```bash
# Clone repository
git clone https://github.com/sairajnaikwade/adaptive-soc-copilot.git
cd adaptive-soc-copilot

# Launch PostgreSQL and FastAPI Backend
docker-compose up -d --build
```

The services will start at:
- **FastAPI Backend API & Docs**: http://localhost:8000/docs
- **PostgreSQL Database**: `localhost:5432` (`soc_copilot_db`)

---

## 💻 Local Development Setup

### Backend (FastAPI + SQLAlchemy + Alembic)

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Run tests
pytest

# Start FastAPI development server
uvicorn app.main:app --reload --port 8000
```

### Frontend (React 19 + Vite + Tailwind CSS)

```bash
cd frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev
```

The frontend will start at http://localhost:5173 with automatic API proxying to `http://localhost:8000`.

---

## 📁 Repository Structure

```text
adaptive-soc-copilot/
├── .github/workflows/        # CI/CD GitHub Actions
├── backend/
│   ├── alembic/              # Alembic schema migrations (17 tables)
│   ├── app/
│   │   ├── api/v1/           # API endpoints (Auth, Tenants, Health)
│   │   ├── core/             # Security, Config, Exceptions, Logging
│   │   ├── db/               # Database engine & session setup
│   │   ├── middleware/       # Logging & Request ID tracing
│   │   ├── models/           # 17 SQLAlchemy ORM models & Enums
│   │   ├── repositories/     # Repository pattern data access layer
│   │   ├── schemas/          # Pydantic v2 request/response schemas
│   │   └── services/         # Business logic layer
│   ├── tests/                # Pytest suite (100% passing)
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/              # Axios client with JWT interceptor
│   │   ├── pages/            # Login & Dashboard views
│   │   ├── store/            # Redux Toolkit state management
│   │   ├── App.tsx
│   │   └── index.css
│   ├── package.json
│   ├── package-lock.json
│   └── vite.config.ts
├── docker-compose.yml
├── SOC_CoPilot_System_Architecture.md
└── README.md
```

---

## 🧪 Running Verification Suite

```bash
# Run backend tests
cd backend
pytest -v
```

---

## 📄 License
This project is licensed under the MIT License.
