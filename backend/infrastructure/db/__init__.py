"""
Public interface for the database package.

Importing from this package gives access to everything needed
to work with the database without reaching into sub-modules directly.
The ORM models are imported here so SQLAlchemy registers all mapped
classes before create_all_tables() is called — this is the clean
alternative to the _orm_models import trick.
"""

from backend.infrastructure.db.database import (  # noqa: F401
    Base,
    SessionFactory,
    create_all_tables,
    engine,
    get_session,
)

# Importing orm_models here ensures all ORM classes are registered
# with SQLAlchemy's metadata before create_all_tables() runs.
# Without this, tables whose ORM class was never imported would not
# be created, even though Base.metadata.create_all() is called.
from backend.infrastructure.db import orm_models  # noqa: F401