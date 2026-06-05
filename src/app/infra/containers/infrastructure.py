from typing import Generator

import redis
from dependency_injector import containers, providers
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


def _session_resource(factory: sessionmaker) -> Generator[Session, None, None]:
    session = factory()
    try:
        yield session
    finally:
        session.close()


class InfrastructureContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    db_engine = providers.Singleton(
        create_engine,
        url=config.database_url,
        future=True,
        echo=False,
    )
    session_factory = providers.Singleton(
        sessionmaker,
        bind=db_engine,
        class_=Session,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )
    redis = providers.Singleton(
        redis.Redis.from_url,
        url=config.redis_url,
        decode_responses=True,
    )
    db_session = providers.Resource(
        _session_resource,
        factory=session_factory,
    )
