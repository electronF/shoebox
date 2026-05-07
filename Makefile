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

# ── Configuration 
APP_MODULE   := backend.main:app
HOST         := 0.0.0.0
DEV_PORT     := 8000
PROD_PORT    := 8000
WORKERS      := 4                  # number of uvicorn worker processes (prod only)
DB_PATH      := data/shoebox.db
UPLOAD_DIR   := data/uploads

# Detect the Python executable (supports both python and python3)
PYTHON := $(shell command -v python3 2>/dev/null || command -v python 2>/dev/null)

# Colours for terminal output
RESET  := \033[0m
BOLD   := \033[1m
GREEN  := \033[32m
YELLOW := \033[33m
RED    := \033[31m
CYAN   := \033[36m

# .PHONY tells make these are not file targets
.PHONY: dev prod test test-cov lint format typecheck \
        db-init db-reset db-shell install clean help

# Default target when running bare `make`
.DEFAULT_GOAL := help

# ── Help 

help:
	@echo ""
	@echo "$(BOLD)Shoebox — available commands$(RESET)"
	@echo ""
	@echo "  $(GREEN)make dev$(RESET)         Start API in development mode (hot reload, port $(DEV_PORT))"
	@echo "  $(GREEN)make prod$(RESET)        Start API in production mode ($(WORKERS) workers, port $(PROD_PORT))"
	@echo ""
	@echo "  $(CYAN)make test$(RESET)        Run the full test suite"
	@echo "  $(CYAN)make test-cov$(RESET)    Run tests with HTML coverage report"
	@echo ""
	@echo "  $(YELLOW)make lint$(RESET)        Check code style (ruff)"
	@echo "  $(YELLOW)make format$(RESET)      Auto-fix code style (ruff)"
	@echo "  $(YELLOW)make typecheck$(RESET)   Static type checking (mypy)"
	@echo ""
	@echo "  $(CYAN)make db-init$(RESET)     Create all database tables"
	@echo "  $(CYAN)make db-reset$(RESET)    $(RED)DROP$(RESET) and recreate all tables — deletes all data"
	@echo "  $(CYAN)make db-shell$(RESET)    Open interactive SQLite shell"
	@echo ""
	@echo "  $(YELLOW)make install$(RESET)     Install all dependencies including dev extras"
	@echo "  $(YELLOW)make clean$(RESET)       Remove cache files and build artifacts"
	@echo ""

# ── Environment setup 

install:
	@echo "$(BOLD)Installing dependencies...$(RESET)"
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e ".[dev]"
	@echo "$(GREEN)Done.$(RESET)"

# Ensure data directories exist before starting the server
_ensure-dirs:
	@mkdir -p $(UPLOAD_DIR)
	@mkdir -p $(dir $(DB_PATH))

# ── Development server 

dev: _ensure-dirs
	@echo "$(BOLD)Starting development server on http://localhost:$(DEV_PORT)$(RESET)"
	@echo "  Swagger UI : http://localhost:$(DEV_PORT)/docs"
	@echo "  ReDoc      : http://localhost:$(DEV_PORT)/redoc"
	@echo ""
	uvicorn $(APP_MODULE) \
		--host $(HOST) \
		--port $(DEV_PORT) \
		--reload \
		--reload-dir backend \
		--log-level debug

# ── Production server 
# Uses multiple workers for concurrency.
# Note: SQLite with WAL mode supports concurrent reads but only one writer.
# For write-heavy workloads, switch to PostgreSQL and increase workers freely.

prod: _ensure-dirs
	@echo "$(BOLD)Starting production server on port $(PROD_PORT) ($(WORKERS) workers)$(RESET)"
	uvicorn $(APP_MODULE) \
		--host $(HOST) \
		--port $(PROD_PORT) \
		--workers $(WORKERS) \
		--log-level warning \
		--no-access-log \
		--proxy-headers

# ── Tests 

test:
	@echo "$(BOLD)Running test suite...$(RESET)"
	pytest backend/tests/ \
		--tb=short \
		--strict-markers \
		-v

test-cov:
	@echo "$(BOLD)Running tests with coverage...$(RESET)"
	pytest backend/tests/ \
		--tb=short \
		--strict-markers \
		-v \
		--cov=backend \
		--cov-report=term-missing \
		--cov-report=html:coverage_report
	@echo ""
	@echo "$(GREEN)HTML report generated: coverage_report/index.html$(RESET)"

# ── Code quality
lint:
	@echo "$(BOLD)Checking code style (ruff)...$(RESET)"
	ruff check backend/

format:
	@echo "$(BOLD)Auto-fixing code style (ruff)...$(RESET)"
	ruff check backend/ --fix
	ruff format backend/

typecheck:
	@echo "$(BOLD)Running static type checks (mypy)...$(RESET)"
	mypy backend/ --ignore-missing-imports

# ── Database 
db-init: _ensure-dirs
	@echo "$(BOLD)Creating database tables...$(RESET)"
	$(PYTHON) -c "from backend.infrastructure.db import create_all_tables; create_all_tables()"
	@echo "$(GREEN)Tables created: $(DB_PATH)$(RESET)"

db-reset: _ensure-dirs
	@echo "$(RED)$(BOLD)WARNING: This will delete all data in $(DB_PATH)$(RESET)"
	@read -p "Type YES to confirm: " confirm && [ "$$confirm" = "YES" ] || (echo "Aborted." && exit 1)
	$(PYTHON) -c "\
from backend.infrastructure.db.database import engine, Base; \
from backend.infrastructure.db import orm_models; \
Base.metadata.drop_all(bind=engine); \
Base.metadata.create_all(bind=engine); \
print('Database reset complete.')"
	@echo "$(GREEN)Done.$(RESET)"

db-shell:
	@echo "$(BOLD)Opening SQLite shell for $(DB_PATH)$(RESET)"
	@echo "Useful queries:"
	@echo "  .tables"
	@echo "  SELECT id, description, amount FROM transactions LIMIT 10;"
	@echo "  .quit"
	@echo ""
	sqlite3 $(DB_PATH)

# ── Cleanup 

clean:
	@echo "$(BOLD)Cleaning cache files...$(RESET)"
	find . -type d -name "__pycache__"   -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache"   -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info"    -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc"         -delete 2>/dev/null || true
	rm -rf coverage_report/ .coverage
	@echo "$(GREEN)Done.$(RESET)"

# ── Frontend ─────────────────────────────────────────────────────────────────

.PHONY: dev prod frontend frontend-only test test-cov lint format typecheck \
        db-init db-reset db-shell install clean help

frontend:
	@echo "$(BOLD)Starting full stack (backend + frontend)$(RESET)"
	@echo "  Backend  → http://localhost:8000"
	@echo "  Frontend → http://localhost:8050"
	@echo ""
	$(MAKE) dev &
	@sleep 2
	PYTHONPATH=. $(PYTHON) frontend/app.py

frontend-only:
	@echo "$(BOLD)Starting Dash frontend on http://localhost:8050$(RESET)"
	@echo "  Requires backend already running on port 8000"
	@echo ""
	PYTHONPATH=. $(PYTHON) frontend/app.py