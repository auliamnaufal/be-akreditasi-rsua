# RSUA Incident Service (FastAPI + MySQL)

Hospital incident reporting backend with JWT auth (access & refresh), RBAC, stateful incident workflow, and optional ML auto-classification.

## Tech Stack

* **FastAPI**, **SQLModel (0.0.21)**, **SQLAlchemy 2.0**
* **MySQL 8** (InnoDB, `utf8mb4`)
* **Alembic** (migrations)
* **Passlib + Argon2** (password hashing)
* **PyJWT** (HS256)
* **scikit-learn** (loads `models/incident_classifier.pkl` if present; fallback rule otherwise)
* **Docker / docker-compose** for local dev

---

## 1) Prerequisites

* Docker Desktop (or Docker Engine) + docker-compose v2
* Make sure ports **3306** (MySQL) and **8000** (API) are free

---

## 2) Clone

```bash
git clone <REPO_URL> be-akreditasi-rsua
cd be-akreditasi-rsua
```

---

## 3) Create `.env`

Create a file named **`.env`** in the project root:

```env
# App
APP_NAME=RSUA Incident Service
ENVIRONMENT=development

# Database (Docker compose points "db" hostname to MySQL container)
DATABASE_URL=mysql+mysqlconnector://user:password@db:3306/akreditasi

# JWT (use strong 64+ char secrets)
JWT_SECRET_KEY=please-change-to-a-64char-random-string
JWT_REFRESH_SECRET_KEY=please-change-to-a-64char-random-string-too
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRES_MINUTES=30
REFRESH_TOKEN_EXPIRES_MINUTES=10080

# Password hashing (recommended)
PASSWORD_HASHING_SCHEME=argon2
TOKEN_VERSION=1

# ML model (optional)
MODEL_PATH=models/incident_classifier.pkl
MODEL_FALLBACK_VERSION=fallback-rule-0.1
```

> Tip: You can use any random 64-char strings for the JWT keys.

---

## 4) Build & Run (Docker)

```bash
# build & start database + API
docker compose up --build -d
```

* API: [http://localhost:8000](http://localhost:8000)
* OpenAPI docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 5) Apply Migrations

```bash
docker compose exec api alembic upgrade head
```

---

## 6) Seed Database (SQL; idempotent)

> This seeds **roles**, an **admin** user (`admin@rsua.local`), and some **departments/locations**.

1. Generate a password hash for the admin user (inside API container):

```bash
ADMIN_HASH=$(docker compose exec -T api python - <<'PY'
import bcrypt; print(bcrypt.hashpw(b"Admin123!", bcrypt.gensalt()).decode())
PY
)
echo "Admin hash: $ADMIN_HASH"
```

2. Seed via SQL (run against the **db** container):

```bash
docker compose exec -T db sh -lc 'mysql --default-character-set=utf8mb4 -uuser -ppassword -D akreditasi' <<SQL
SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;
SET collation_connection = 'utf8mb4_unicode_ci';

START TRANSACTION;

-- ROLES
INSERT INTO roles (name, description, created_at, updated_at)
VALUES
  ('perawat','Perawat - dapat membuat laporan insiden', NOW(), NOW()),
  ('pj','Penanggung jawab unit - review awal', NOW(), NOW()),
  ('mutu','Tim mutu - review lanjutan', NOW(), NOW()),
  ('admin','Administrator sistem', NOW(), NOW())
ON DUPLICATE KEY UPDATE description=VALUES(description), updated_at=VALUES(updated_at);

-- ADMIN USER
SET @ADMIN_EMAIL := 'admin@rsua.local';
SET @ADMIN_NAME  := 'System Admin';
SET @ADMIN_HASH  := '${ADMIN_HASH}';

INSERT INTO users (email, full_name, hashed_password, is_active, token_version, last_password_change, created_at, updated_at)
VALUES (@ADMIN_EMAIL, @ADMIN_NAME, @ADMIN_HASH, TRUE, 1, NOW(), NOW(), NOW())
ON DUPLICATE KEY UPDATE full_name=@ADMIN_NAME, hashed_password=@ADMIN_HASH, updated_at=NOW();

-- MAP ADMIN → admin ROLE
INSERT IGNORE INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM users u
JOIN roles r ON r.name COLLATE utf8mb4_unicode_ci = 'admin' COLLATE utf8mb4_unicode_ci
WHERE u.email COLLATE utf8mb4_unicode_ci = @ADMIN_EMAIL COLLATE utf8mb4_unicode_ci;

-- DEPARTMENTS
INSERT INTO departments (name, description, created_at, updated_at)
VALUES
  ('IGD', 'Instalasi Gawat Darurat', NOW(), NOW()),
  ('ICU', 'Intensive Care Unit',     NOW(), NOW()),
  ('Farmasi', 'Unit Farmasi',        NOW(), NOW()),
  ('Bedah', 'Bedah Sentral',         NOW(), NOW())
ON DUPLICATE KEY UPDATE description=VALUES(description), updated_at=VALUES(updated_at);

-- LOCATIONS
INSERT INTO locations (name, description, created_at, updated_at)
VALUES
  ('Ruang Mawar', 'Ruang rawat inap Mawar', NOW(), NOW()),
  ('Ruang Melati', 'Ruang rawat inap Melati', NOW(), NOW()),
  ('Laboratorium', 'Lab Klinik', NOW(), NOW()),
  ('Radiologi', 'Unit Radiologi', NOW(), NOW())
ON DUPLICATE KEY UPDATE description=VALUES(description), updated_at=VALUES(updated_at);

COMMIT;
SQL
```

3. Verify:

```bash
docker compose exec -T db sh -lc 'mysql -uuser -ppassword -D akreditasi -e "
SELECT id, name FROM roles ORDER BY id;
SELECT id, email, full_name FROM users WHERE email = \"admin@rsua.local\";
SELECT ur.user_id, ur.role_id FROM user_roles ur
JOIN users u ON u.id=ur.user_id AND u.email=\"admin@rsua.local\";
"'
```

---

## 7) Quick API Smoke Test

Register a nurse (perawat) or log in as admin.

```bash
# Register (example)
curl -X POST http://localhost:8000/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"nurse1@rsua.local","full_name":"Nurse One","password":"S3cretPass!","roles":["perawat"]}'

# Login as admin
curl -X POST http://localhost:8000/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@rsua.local","password":"Admin123!"}'
```

Use the returned **access token**:

```
Authorization: Bearer <access_token>
```

---

## 8) Development Flow

* Code is mounted into the API container (hot reload).
* Server reloads on changes (`uvicorn --reload`).
* Run tests:

```bash
docker compose exec api pytest -q
```

---

## 9) (Optional) Running Locally Without Docker

> You’ll need MySQL running locally and a DB named `akreditasi`.

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip

# Install deps
pip install -r requirements.txt

# Configure .env to use your local MySQL host/credentials:
# DATABASE_URL=mysql+mysqlconnector://user:password@127.0.0.1:3306/akreditasi

alembic upgrade head
uvicorn src.app.main:app --host 0.0.0.0 --port 8000 --reload
```

To seed locally, reuse the SQL snippet above but point to your local MySQL.

---

## 10) Configuration Notes

* **Settings** are loaded from `.env` via `pydantic-settings`.
* **Password hashing:** use `PASSWORD_HASHING_SCHEME=argon2` (recommended). If you must use bcrypt, prefer `bcrypt_sha256` to remove the 72-byte limit.
* **JWT:** HS256; rotate secrets by changing `JWT_SECRET_KEY` / `JWT_REFRESH_SECRET_KEY`. Refresh token rotation supported.
* **ML model:** if `models/incident_classifier.pkl` is missing, the service uses a fallback heuristic with version `MODEL_FALLBACK_VERSION`.

---

## 11) Troubleshooting

**Collation error 1267 (mix of collations)**

Run once to normalize:

```bash
docker compose exec -T db sh -lc 'mysql -uuser -ppassword -D akreditasi -e "
ALTER DATABASE akreditasi CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE roles       CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE users       CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE user_roles  CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE departments CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE locations   CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE incidents   CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
"'
```

**bcrypt issues or 72-byte password limit**

Set in `.env`:

```
PASSWORD_HASHING_SCHEME=argon2
```

(or `bcrypt_sha256` if you must keep bcrypt), then rebuild.

**Imports / code changes not reflected**

Rebuild if hot reload misses something:

```bash
docker compose down
docker compose up --build -d
```

**Ports already in use**

Change `ports` in `docker-compose.yml`, e.g. `8001:8000`.

---

## 12) Project Structure (key paths)

```
.
├─ .env
├─ docker-compose.yml
├─ Dockerfile
├─ requirements.txt
├─ models/
│  └─ incident_classifier.pkl      # optional
├─ alembic/
│  ├─ env.py
│  └─ versions/
│     ├─ 0001_init.py
│     └─ 0002_audit_indexing.py
└─ src/app/
   ├─ main.py
   ├─ config.py
   ├─ db.py
   ├─ models/
   │  ├─ base.py
   │  ├─ user.py
   │  ├─ role.py
   │  ├─ incident.py
   │  ├─ department.py
   │  └─ location.py
   ├─ schemas/
   ├─ routers/
   ├─ security/
   │  ├─ jwt.py
   │  └─ passwords.py
   └─ services/
      └─ ml.py
```

---

## 13) Handy Commands

```bash
# logs
docker compose logs -f api
docker compose logs -f db

# exec shells
docker compose exec api sh
docker compose exec db bash

# reset everything
docker compose down -v  # WARNING: drops DB volume
docker compose up --build -d
```
