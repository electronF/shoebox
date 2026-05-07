"""
Point d'entrée de l'application FastAPI — App Factory Pattern.

Utilise le pattern "app factory" pour faciliter les tests :
`create_app()` est appelée dans les tests avec des overrides
de dépendances, et au démarrage normal via `app = create_app()`.
"""

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import settings
from backend.infrastructure.db.database import create_all_tables
from backend.api.routers import (
    actions,
    analytics,
    files,
    health,
    invoices,
    sources,
    transactions,
)

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    """
    Gestionnaire de cycle de vie de l'application.

    Exécuté au démarrage (avant) et à l'arrêt (après le yield).
    Remplace les anciens @app.on_event("startup").
    """
    logger.info("Démarrage Shoebox API v%s", settings.app_version)
    create_all_tables()
    yield
    logger.info("Arrêt Shoebox API")


def create_app() -> FastAPI:
    """
    Construit et configure l'application FastAPI.

    Returns:
        Instance FastAPI prête à être servie par uvicorn
        ou utilisée dans les tests.
    """
    app = FastAPI(
        title=settings.app_title,
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS — à restreindre en production
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8050"],   # frontend Dash
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Enregistrement des routers avec leurs préfixes et tags OpenAPI
    app.include_router(health.router,       tags=["Health"])
    app.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])
    app.include_router(invoices.router,     prefix="/invoices",     tags=["Invoices"])
    app.include_router(sources.router,      prefix="/sources",      tags=["Sources"])
    app.include_router(files.router,        prefix="/files",        tags=["Files"])
    app.include_router(analytics.router,    prefix="/analytics",    tags=["Analytics"])
    app.include_router(actions.router,      prefix="/actions",      tags=["Actions"])

    return app


# Instance unique utilisée par uvicorn
app = create_app()