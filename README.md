# Shoebox

**Freelance financial manager** — turns a folder of raw financial documents (bank statements, receipts, invoices, notes) into a structured, queryable database with a dashboard frontend.

> **Status:** Backend complete · Frontend in progress

---

## Table of contents

1. [Tech stack](#tech-stack)
2. [Project structure](#project-structure)
3. [Prerequisites](#prerequisites)
4. [Environment setup](#environment-setup)
5. [Configuration](#configuration)
6. [Running the application](#running-the-application)
7. [Available make commands](#available-make-commands)
8. [Running the tests](#running-the-tests)
9. [API reference](#api-reference)
10. [Architecture notes](#architecture-notes)
11. [Roadmap](#roadmap)

---

## Tech stack

| Layer | Technology |
|---|---|
| API framework | FastAPI 0.111 + uvicorn |
| Data validation | Pydantic v2 |
| ORM | SQLAlchemy 2.x (Mapped / mapped_column) |
| Database | SQLite (WAL mode) — swappable for PostgreSQL/MySQL via one env var |
| PDF parsing | pdfplumber |
| Image OCR | pytesseract + Pillow |
| Spreadsheet parsing | openpyxl |
| Testing | pytest + pytest-asyncio + httpx |
| Linting / formatting | ruff |
| Type checking | mypy (strict) |
| Frontend | Dash + Plotly (in progress) |

---

## Project structure

```
shoebox/
│
├── .env                         # environment variables (DATABASE_URL, DEBUG …)
├── .env.example                 # template — safe to commit
├── Makefile                     # developer task runner
├── pyproject.toml               # dependencies + ruff/mypy config
├── README.md
│
├── data/
│   ├── shoebox.db               # SQLite database (gitignored)
│   └── uploads/                 # physical uploaded files (gitignored)
│
└── backend/
    ├── main.py                  # FastAPI app factory + lifespan + router registration
    ├── core/                    # Pure domain — zero external dependencies
    │   ├── config.py            # pydantic-settings: Settings singleton
    │   ├── enums.py             # Category, SourceType, EntryMethod, DocType …
    │   ├── models.py            # Pure dataclasses: Transaction, Invoice, ActionItem …
    │   └── interfaces.py        # ABCs: ITransactionRepository, IParser, IFileStorage …
    ├── schemas/                 # Pydantic v2 — API input/output validation only
    │   ├── common.py            # PaginatedResponse[T], ErrorDetail, HealthCheck
    │   ├── transaction.py       # TransactionCreate / Update / Read
    │   ├── invoice.py           # InvoiceCreate / Update / Read
    │   ├── source.py            # PaymentSourceCreate / Read
    │   ├── file.py              # UploadedFileRead, IngestionResult
    │   └── analytics.py         # AnalyticsSummary, CategoryBreakdown
    ├── infrastructure/          # Concrete implementations (OCP)
    │   ├── db/
    │   │   ├── database.py      # SQLAlchemy engine + WAL config + session factory
    │   │   ├── orm_models.py    # SQLAlchemy ORM classes
    │   │   ├── id_generator.py  # generate_id() → "REC-250122-00001"
    │   │   └── repositories.py  # SQL implementations of core interfaces
    │   ├── parsers/             # PDF, Image/OCR, XLSX, TXT parsers
    │   ├── categorization/      # Keyword rules + transaction validator
    │   └── storage.py           # DiskFileStorage
    ├── services/                # Business logic — SRP, depends only on interfaces
    │   ├── ingestion_service.py
    │   ├── transaction_service.py
    │   ├── invoice_service.py
    │   ├── analytics_service.py
    │   ├── recurring_service.py
    │   └── action_service.py
    ├── api/                     # FastAPI layer — thin controllers only
    │   ├── dependencies.py      # Depends() factories
    │   └── routers/             # health, transactions, invoices, sources, files, analytics, actions
    └── tests/
        ├── conftest.py          # in-memory DB fixtures, SAVEPOINT isolation
        ├── test_id_generator.py
        ├── test_categorization.py
        ├── test_ingestion_service.py
        └── test_transaction_router.py
```

---

## Prerequisites

Before you start, make sure the following are installed on your machine.

### Python 3.11+

```bash
python3 --version
# Python 3.11.x or higher required
```

Download from [python.org](https://www.python.org/downloads/) if needed.

### Tesseract OCR

Required for parsing receipt images. Install the French language pack as well.

**macOS (Homebrew)**
```bash
brew install tesseract tesseract-lang
```

**Ubuntu / Debian**
```bash
sudo apt update
sudo apt install tesseract-ocr tesseract-ocr-fra
```

**Windows**
Download the installer from [github.com/UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki).
Add the install directory to your `PATH`.

Verify:
```bash
tesseract --version
```

### SQLite (CLI, optional)

Only needed for `make db-shell`. Usually pre-installed on macOS and Linux.

```bash
sqlite3 --version
```

---

## Environment setup

### 1. Clone the repository

```bash
git clone https://github.com/youruser/shoebox.git
cd shoebox
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
```

### 3. Activate the virtual environment

**macOS / Linux**
```bash
source .venv/bin/activate
```

**Windows (PowerShell)**
```powershell
.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt)**
```cmd
.venv\Scripts\activate.bat
```

You should see `(.venv)` in your terminal prompt.

### 4. Install dependencies

```bash
make install
# or without make:
pip install -e ".[dev]"
```

This installs the application and all development dependencies (pytest, ruff, mypy, httpx).

### 5. Create the data directories

The Makefile handles this automatically, but you can also do it manually:

```bash
mkdir -p data/uploads
```

---

## Configuration

### Copy the example env file

```bash
cp .env.example .env
```

### Edit `.env`

```bash
# Database — SQLite by default
# To switch to PostgreSQL, change this one line. No application code changes.
DATABASE_URL=sqlite:///./data/shoebox.db
# DATABASE_URL=postgresql://user:password@localhost:5432/shoebox

# Directory where uploaded files are stored on disk
UPLOAD_DIR=./data/uploads

# Set to true to enable SQL query logging in the terminal
DEBUG=false

# Set to true only when running the test suite
TESTING=false

# API metadata (shown in /docs)
APP_TITLE=Shoebox API
APP_VERSION=0.1.0
```

> **Switching databases:** changing `DATABASE_URL` to a PostgreSQL or MySQL URL is the only change required. SQLAlchemy generates the correct DDL and SQL dialect automatically. All application code, services, and repositories remain identical.

---

## Running the application

### Development mode

Hot reload is enabled — the server restarts automatically whenever you edit a Python file in `backend/`.

```bash
make dev
```

The server starts on `http://localhost:8000`.

| URL | Description |
|---|---|
| `http://localhost:8000/docs` | Swagger UI — interactive API explorer |
| `http://localhost:8000/redoc` | ReDoc — clean read-only documentation |
| `http://localhost:8000/health` | Health check endpoint |

### Production mode

Runs with 4 worker processes and reduced logging. Suitable for deployment behind a reverse proxy (nginx, Caddy).

```bash
make prod
```

> **Note on SQLite in production:** SQLite with WAL mode handles concurrent reads well and serialises concurrent writes without errors. For write-heavy production workloads, switch to PostgreSQL via `DATABASE_URL`.

### Initialize the database

Tables are created automatically on startup via the FastAPI lifespan handler. You can also create them manually:

```bash
make db-init
```

---

## Available make commands

```
# =============================================================================
# Shoebox — Developer task runner
# =============================================================================
# Usage:
#   make dev          start the API server in development mode (hot reload)
#   make prod         start the API server in production mode
#   make test         run the full test suite
#   make test-cov     run tests with coverage report
#   make lint         check code style with ruff
#   make format       auto-fix code style with ruff
#   make typecheck    run mypy static type checking
#   make db-init      create all database tables
#   make db-reset     drop and recreate all tables (WARNING: deletes all data)
#   make db-shell     open an interactive SQLite shell
#   make install      install all dependencies (dev included)
#   make clean        remove cache files and temporary artifacts
# =============================================================================
```

### Quick reference

| Command | What it does |
|---|---|
| `make dev` | Starts uvicorn with `--reload` on port 8000 |
| `make prod` | Starts uvicorn with 4 workers, no reload, reduced logging |
| `make test` | Runs pytest against an in-memory SQLite DB |
| `make test-cov` | Same + generates `coverage_report/index.html` |
| `make lint` | Checks code style with ruff (no changes applied) |
| `make format` | Auto-fixes code style and formatting with ruff |
| `make typecheck` | Runs mypy static type analysis |
| `make db-init` | Creates all tables (idempotent, safe to run multiple times) |
| `make db-reset` | **Drops all tables and data** — prompts for confirmation |
| `make db-shell` | Opens `sqlite3` interactive shell on `data/shoebox.db` |
| `make install` | Installs the project and all dev dependencies |
| `make clean` | Removes `__pycache__`, `.pytest_cache`, `.mypy_cache`, coverage files |

---

## Running the tests

Tests use an in-memory SQLite database. No `.env` file, no running server, and no disk writes are needed.

```bash
# Run all tests
make test

# Run with coverage report
make test-cov

# Run a specific test file
pytest backend/tests/test_categorization.py -v

# Run a specific test by name
pytest backend/tests/test_categorization.py::test_categorize_known_merchants -v

# Stop on first failure
pytest backend/tests/ -x
```

### Test isolation strategy

Each test runs inside a database `SAVEPOINT`. Even if the code under test calls `session.commit()`, all changes are rolled back after the test completes. This gives full isolation without dropping and recreating the schema between tests.

### Coverage report

```bash
make test-cov
open coverage_report/index.html   # macOS
xdg-open coverage_report/index.html  # Linux
```

---

## API reference

The full interactive documentation is available at `http://localhost:8000/docs` when the server is running.

### Endpoints summary

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | API health check |
| `GET` | `/transactions` | List transactions (paginated, filterable) |
| `POST` | `/transactions` | Create a manual transaction |
| `GET` | `/transactions/{id}` | Get a transaction by ID |
| `PATCH` | `/transactions/{id}` | Partially update a transaction |
| `DELETE` | `/transactions/{id}` | Delete a transaction |
| `GET` | `/invoices` | List issued invoices |
| `POST` | `/invoices` | Create an invoice |
| `PATCH` | `/invoices/{id}` | Update an invoice |
| `GET` | `/sources` | List payment sources |
| `POST` | `/sources` | Register a payment source |
| `POST` | `/files/upload` | Upload and ingest one or more files |
| `GET` | `/files` | List all ingested files |
| `GET` | `/analytics/summary` | Global financial KPIs |
| `GET` | `/analytics/by-category` | Expenses grouped by category |
| `GET` | `/analytics/by-month` | Expenses grouped by month |
| `GET` | `/analytics/by-source` | Expenses grouped by payment source |
| `GET` | `/actions` | List action items (todos) |
| `POST` | `/actions` | Create an action item |
| `PATCH` | `/actions/{id}/status` | Mark an action as done or reopen it |

### ID format

All entity IDs follow the pattern `PREFIX-YYMMDD-NNNNN`:

| Prefix | Entity | Example |
|---|---|---|
| `TXN` | Transaction (manual) | `TXN-250506-00001` |
| `REC` | Receipt transaction | `REC-250122-00001` |
| `STMT` | Statement file | `STMT-250101-00001` |
| `INV` | Invoice | `INV-250101-00001` |
| `SRC` | Payment source | `SRC-250101-00001` |
| `ANO` | Anomaly | `ANO-250101-00001` |
| `ACT` | Action item | `ACT-250101-00001` |

### Accepted file formats by document type

| Document type | Accepted formats |
|---|---|
| Receipt (`REC`) | `.jpg`, `.jpeg`, `.png`, `.pdf` |
| Statement (`STMT`) | `.pdf`, `.xlsx` |
| Invoice (`INV`) | `.pdf`, `.xlsx` |
| Notes (`NOTE`) | `.txt` |

---

## Architecture notes

### Layer dependency rule

```
Routers → Services → Core interfaces ← Infrastructure implementations
```

- **Routers** never import repositories directly.
- **Services** never import FastAPI or Pydantic.
- **Core** (`models.py`, `interfaces.py`, `enums.py`) has zero external dependencies.
- **Infrastructure** implements the core interfaces and depends on SQLAlchemy, pytesseract, pdfplumber, etc.

### Three model types — not one

| File | Type | Purpose |
|---|---|---|
| `core/models.py` | Python `@dataclass` | Domain objects — travel between layers |
| `infrastructure/db/orm_models.py` | SQLAlchemy `Mapped` classes | Speak to the database |
| `schemas/*.py` | Pydantic `BaseModel` | Validate API input, serialise API output |

Conversion between layers happens in repositories (`ORM → dataclass`) and routers (`dataclass → Pydantic Read schema`).

### Switching databases

Change one line in `.env`:

```bash
# From
DATABASE_URL=sqlite:///./data/shoebox.db

# To
DATABASE_URL=postgresql://user:password@localhost:5432/shoebox
```

SQLAlchemy handles the DDL and SQL dialect differences. No application code changes.

---

## Roadmap

- [x] Core domain models and interfaces
- [x] SQLAlchemy ORM with `Mapped` / `mapped_column` (2.x style)
- [x] ID generator (`PREFIX-YYMMDD-NNNNN`)
- [x] PDF statement parser (pdfplumber)
- [x] Image receipt parser (Tesseract OCR)
- [x] XLSX invoice parser (openpyxl)
- [x] Notes parser (action item extraction)
- [x] Keyword-based categorisation engine
- [x] Transaction validation (taxes, dates, amounts)
- [x] Ingestion pipeline with per-file error handling
- [x] FastAPI backend with full CRUD endpoints
- [x] Analytics endpoints (summary, by-category, by-month, by-source)
- [x] Recurring pattern detection + 3-month forecast
- [x] pytest suite with SAVEPOINT isolation
- [ ] Dash frontend — upload flow
- [ ] Dash frontend — dashboard views (overview, recurring, cards, files)
- [ ] Anomaly resolution UI
- [ ] Export to XLSX (tax report)
- [ ] PostgreSQL support (tested end-to-end)
- [ ] Docker / docker-compose setup
