# RSUA Incident Reporting Service

Production-ready FastAPI backend for hospital incident reporting aligned with RS accreditation categories (KTD, KTC, KNC, KPCS, Sentinel). Features include JWT authentication, RBAC, incident lifecycle management, ML-assisted classification, and full Dockerized deployment.

## Features

- FastAPI + SQLModel (SQLAlchemy 2.0 style) with MySQL 8 support.
- JWT access/refresh tokens with rotation and revocation on logout/password change.
- Role-based access (perawat, pj, mutu, admin) with route dependencies.
- Incident workflow: draft → submitted → PJ reviewed → Mutu reviewed → closed.
- ML integration via scikit-learn pipeline loader with heuristic fallback (`models/incident_classifier.pkl`).
- Alembic migrations (`0001_init`, `0002_audit_indexing`) and seeding script (`scripts/seed.py`).
- Comprehensive TRD-style API contracts in `docs/trd`.
- Dockerfile + docker-compose for local development.
- Pytest suite covering auth, RBAC, and lifecycle guards.

## Getting Started

### Prerequisites

- Docker and Docker Compose (recommended) or Python 3.11 with MySQL 8.

### Environment Configuration

Copy the example environment file and adjust secrets:

```bash
cp .env.example .env
```

### Running with Docker Compose

```bash
docker-compose up --build
```

API will be available at `http://localhost:8000`. OpenAPI docs at `/docs`.

### Database Migration & Seed

Inside the container or local environment:

```bash
alembic upgrade head
python scripts/seed.py
```

This seeds default roles and an administrator (`admin@rsua.local` / `Admin123!`).

### Running Tests

```bash
pytest
```

### ML Model Placeholder

Place your trained scikit-learn pipeline at `models/incident_classifier.pkl`. See `src/app/services/ml.py` for loader details and replace the heuristic fallback when ready. Provide a training notebook reference when integrating a real model.

## Key Directories

- `src/app` – application code (routers, models, schemas, services, security).
- `alembic` – migration environment and versions.
- `docs/trd` – API contracts (TRD format).
- `tests` – pytest suite.
- `scripts` – database seeders.

## Security Notes

- Argon2/Bcrypt hashing via Passlib.
- JWT claims include `sub`, `role`, `roles`, `jti`, and `token_version` for revocation.
- Middleware attaches decoded claims to `request.state.claims` for downstream use.

## Accreditation Categories

Incident category enums and reference endpoints follow RS accreditation standards: KTD, KTC, KNC, KPCS, Sentinel.
