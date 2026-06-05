from typing import Generator

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.infra.containers import get_container


def get_engine() -> Engine:
    return get_container().infra.db_engine()


def get_session_factory() -> sessionmaker[Session]:
    return get_container().infra.session_factory()


def get_session() -> Generator[Session, None, None]:
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()
