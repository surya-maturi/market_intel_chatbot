import os
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.db.models import Base

# Plain sync SQLAlchemy + a threadpool at call sites, not aiosqlite: asyncpraw
# pins aiosqlite<=0.17.0, which is incompatible with SQLAlchemy's async
# connection-termination path and crashes with AttributeError on any
# cancelled/dropped request. Going sync avoids the version conflict entirely.
_engine = None
_session_factory = None


def _get_engine():
    global _engine, _session_factory
    if _engine is None:
        settings = get_settings()
        os.makedirs(os.path.dirname(settings.db_path) or ".", exist_ok=True)
        _engine = create_engine(f"sqlite:///{settings.db_path}", connect_args={"check_same_thread": False})
        _session_factory = sessionmaker(_engine, expire_on_commit=False)
    return _engine


def init_db() -> None:
    engine = _get_engine()
    Base.metadata.create_all(engine)


def get_session_factory() -> sessionmaker[Session]:
    _get_engine()
    assert _session_factory is not None
    return _session_factory


def get_session() -> Iterator[Session]:
    with get_session_factory()() as session:
        yield session
