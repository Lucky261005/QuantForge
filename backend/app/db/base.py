"""Single import point for Alembic autogenerate — importing this module registers
every model's table on Base.metadata."""

from app.db.base_class import Base  # noqa: F401 — re-exported for `from app.db.base import Base`
from app.models import *  # noqa: F401,F403
