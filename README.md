# Shoebox

**Freelance financial manager** — turns a folder of raw financial documents (bank statements, receipts, invoices, notes) into a structured, queryable database with a full dashboard frontend and a Chrome extension for at-a-glance KPIs.

> **Status:** Backend complete · Frontend complete · Chrome extension ready

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
9. [Chrome extension](#chrome-extension)
10. [API reference](#api-reference)
11. [Architecture notes](#architecture-notes)
12. [Roadmap](#roadmap)

---

## Tech stack

| Layer | Technology |
|---|---|
| API framework | FastAPI 0.111+ + uvicorn |
| Data validation | Pydantic v2 |
| ORM | SQLAlchemy 2.x (Mapped / mapped_column) |
| Database | SQLite (WAL mode) — swappable for PostgreSQL via one env var |
| PDF parsing | PyMuPDF |
| Image OCR | pytesseract + Pillow |
| Spreadsheet parsing | openpyxl |
| Testing | pytest + pytest-asyncio + httpx |
| Linting / formatting | ruff |
| Type checking | mypy (strict) |
| Frontend | Dash 2.17 + Plotly 5.22 |
| Browser extension | Chrome Extension (Manifest V3) |

---

## Project structure

```
shoebox/
│
├── .env                         # environment variables (DATABASE_URL, DEBUG …)
├── .env.example                 # template — safe to commit
├── Makefile                     # developer task runner
├── pyproject.toml               # dependencies + ruff/mypy config
├── requirements.txt             # pinned flat dependency list
├── README.md
│
├── data/
│   ├── shoebox.db               # SQLite database (gitignored)
│   └── uploads/                 # physical uploaded files (gitignored)
│
├── chrome-extension/            # Chrome Extension (Manifest V3)
│   ├── manifest.json
│   ├── popup.html
│   ├── popup.css
│   ├── popup.js
│   └── icons/                   # 16 / 48 / 128 px PNG icons
│
├── frontend/                    # Dash application (port 8050)
│   ├── app.py                   # Entry point + router + nav callbacks
│   ├── layout.py                # Persistent shell (sidebar, stores)
│   ├── theme.py                 # Design system — colors, fonts, spacing
│   ├── api_client.py            # HTTP client wrapping the FastAPI backend
│   ├── assets/                  # Global CSS
│   ├── components/              # Reusable Dash components
│   └── views/                   # One module per page
│       ├── overview.py          # Main dashboard
│       ├── invoices.py          # Issued invoice tracking
│       ├── invoices_callbacks.py
│       ├── subscriptions.py
│       ├── recurring.py
│       ├── report.py
│       ├── sources.py
│       ├── files.py
│       └── upload/              # 4-step ingestion wizard
│
└── backend/
    ├── main.py                  # FastAPI app factory + lifespan
    ├── core/                    # Pure domain — zero external dependencies
    ├── schemas/                 # Pydantic v2 — API input/output only
    ├── infrastructure/          # DB, parsers, storage (OCP)
    ├── services/                # Business logic (SRP)
    ├── api/                     # FastAPI routers — thin controllers
    └── tests/
```

---

## Prerequisites

### Python 3.11+

```bash
python3 --version
# Python 3.11.x or higher required
```

### Tesseract OCR

Required for parsing receipt images.

**macOS (Homebrew)**
```bash
brew install tesseract tesseract-lang
```

**Ubuntu / Debian**
```bash
sudo apt update && sudo apt install tesseract-ocr tesseract-ocr-fra
```

**Windows** — installer at [github.com/UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki). Add install dir to `PATH`.

---

## Environment setup

```bash
# 1. Clone
git clone https://github.com/youruser/shoebox.git
cd shoebox

# 2. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate.bat     # Windows

# 3. Install all dependencies (including dev)
make install

# 4. Copy env config
cp .env.example .env
```

---

## Configuration

Edit `.env`:

```bash
DATABASE_URL=sqlite:///./data/shoebox.db   # or postgresql://...
UPLOAD_DIR=./data/uploads
DEBUG=false
TESTING=false
APP_TITLE=Shoebox API
APP_VERSION=1.0.0
```

---

## Running the application

The app has two independent processes — run both to get the full experience.

### Option A — Full stack (recommended)

```bash
make frontend
```

Starts the FastAPI backend on port 8000, waits 2 seconds, then starts the Dash frontend on port 8050.

### Option B — Separate terminals

**Terminal 1 — Backend:**
```bash
make dev
```

**Terminal 2 — Frontend:**
```bash
make frontend-only
```

### Access points

| URL | Description |
|---|---|
| `http://localhost:8050` | Dash dashboard (main UI) |
| `http://localhost:8000/docs` | Swagger UI — interactive API explorer |
| `http://localhost:8000/redoc` | ReDoc — read-only API docs |
| `http://localhost:8000/health` | Health check |

### Dashboard pages

| Path | Description |
|---|---|
| `/` | Vue d'ensemble — KPIs, charts, alerts, opportunities |
| `/upload` | Import wizard — step-by-step file ingestion |
| `/invoices` | Issued invoices — KPIs, monthly chart, mark-as-paid |
| `/subscriptions` | Recurring subscriptions |
| `/recurring` | Recurring pattern detection + 3-month forecast |
| `/report` | Tax report |
| `/sources` | Payment sources & cards |
| `/files` | Ingested file history |

---

## Available make commands

| Command | What it does |
|---|---|
| `make dev` | Backend only — uvicorn with `--reload` on port 8000 |
| `make prod` | Backend — uvicorn with 4 workers, no reload |
| `make frontend` | Full stack — backend + frontend (both ports) |
| `make frontend-only` | Frontend only — requires backend already running |
| `make test` | Full test suite against in-memory SQLite |
| `make test-cov` | Tests + HTML coverage report |
| `make lint` | ruff code style check |
| `make format` | ruff auto-fix |
| `make typecheck` | mypy static type analysis |
| `make db-init` | Create all database tables |
| `make db-reset` | **Drop all data** and recreate tables |
| `make db-shell` | Interactive SQLite shell |
| `make install` | Install project + all dev dependencies |
| `make clean` | Remove `__pycache__`, `.pytest_cache`, coverage files |

---

## Running the tests

Tests run against an in-memory SQLite database — no `.env`, no running server required.

```bash
make test                                              # full suite
make test-cov                                          # with HTML report
pytest backend/tests/test_categorization.py -v        # single file
pytest backend/tests/ -x                               # stop on first failure
```

Each test runs inside a `SAVEPOINT` and is fully rolled back after completion.

---

## Chrome extension

The extension shows a quick overview popup — KPIs, open action items, and unpaid invoices — without leaving your current browser tab. It connects to the local backend on port 8000.

### Installation

1. Open Chrome and go to `chrome://extensions`
2. Enable **Developer mode** (toggle in the top-right corner)
3. Click **Load unpacked**
4. Select the `chrome-extension/` folder inside this repository
5. The Shoebox icon appears in your toolbar

> The extension requires the backend to be running (`make dev` or `make frontend`).  
> It does **not** require an internet connection — all data comes from `localhost:8000`.

### Extension features

| Feature | Description |
|---|---|
| KPI cards | Business expenses, amount to collect, refunds, flagged items |
| À faire | First 4 open action items from uploaded notes |
| Factures en attente | Unpaid and overdue invoices with amounts |
| Open dashboard | Button opens `http://localhost:8050` in a new tab |
| Refresh | Manually re-fetches all data from the backend |
| Error state | Clear message if the backend is not running |

---

## API reference

Full interactive docs at `http://localhost:8000/docs` when the server is running.

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/transactions` | List transactions (paginated, filterable) |
| `POST` | `/transactions` | Create a manual transaction |
| `PATCH` | `/transactions/{id}` | Update a transaction |
| `DELETE` | `/transactions/{id}` | Delete a transaction |
| `GET` | `/invoices` | List issued invoices |
| `POST` | `/invoices` | Create an invoice |
| `PATCH` | `/invoices/{id}` | Update an invoice (status, date_paid…) |
| `GET` | `/sources` | List payment sources |
| `POST` | `/sources` | Register a payment source |
| `POST` | `/files/upload` | Upload and ingest one or more files |
| `GET` | `/files` | List ingested files |
| `POST` | `/files/parse` | Parse a file preview without saving |
| `GET` | `/analytics/summary` | Global financial KPIs |
| `GET` | `/analytics/by-category` | Expenses by category |
| `GET` | `/analytics/by-month` | Expenses by month |
| `GET` | `/analytics/by-source` | Expenses by payment source |
| `GET` | `/analytics/recurring` | Recurring patterns + 3-month forecast |
| `GET` | `/actions` | List action items (todos from notes) |
| `PATCH` | `/actions/{id}/status` | Mark an action done or reopen |

### Accepted file formats

| Document type | Accepted formats |
|---|---|
| Receipt (`REC`) | `.jpg`, `.jpeg`, `.png`, `.pdf` |
| Statement (`STMT`) | `.pdf`, `.xlsx` |
| Invoice (`INV`) | `.pdf`, `.xlsx` |
| Notes (`NOTE`) | `.txt` |

### ID format

All IDs follow `PREFIX-YYMMDD-NNNNN` — e.g. `INV-250506-00003`.

---

## Architecture notes

### Layer dependency rule

```
Routers → Services → Core interfaces ← Infrastructure implementations
```

- **Routers** never import repositories directly.
- **Services** never import FastAPI or Pydantic.
- **Core** (`models.py`, `interfaces.py`, `enums.py`) has zero external dependencies.
- **Infrastructure** implements core interfaces using SQLAlchemy, pytesseract, PyMuPDF, etc.

### Three model types

| File | Type | Purpose |
|---|---|---|
| `core/models.py` | Python `@dataclass` | Domain objects — travel between layers |
| `infrastructure/db/orm_models.py` | SQLAlchemy `Mapped` | Speak to the database |
| `schemas/*.py` | Pydantic `BaseModel` | Validate API input, serialise API output |

### Switching databases

Change one line in `.env`:

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/shoebox
```

No application code changes required.

---

## Roadmap

- [x] Core domain models and interfaces
- [x] SQLAlchemy ORM with `Mapped` / `mapped_column` (2.x style)
- [x] ID generator (`PREFIX-YYMMDD-NNNNN`)
- [x] PyMuPDF PDF parser
- [x] Image receipt parser (Tesseract OCR)
- [x] XLSX invoice/statement parser (openpyxl)
- [x] Notes parser (action item extraction from `[todo]` / `[done]`)
- [x] Keyword-based categorisation engine
- [x] Transaction validation (taxes, dates, amounts)
- [x] Ingestion pipeline with per-file error handling
- [x] FastAPI backend — full CRUD + analytics endpoints
- [x] Recurring pattern detection + 3-month forecast
- [x] pytest suite with SAVEPOINT isolation
- [x] Dash frontend — 4-step import wizard (type → upload → preview → forms)
- [x] Dash frontend — overview dashboard with anomaly detection
- [x] Dash frontend — issued invoice tracking (KPIs, chart, mark-as-paid)
- [x] Dash frontend — subscriptions, recurring, report, sources, files pages
- [x] Chrome extension — KPI overview + open-dashboard button
- [ ] Export to XLSX (tax report download)
- [ ] PostgreSQL end-to-end validation
- [ ] Docker / docker-compose setup
- [ ] Multi-period support (fiscal year selector)
