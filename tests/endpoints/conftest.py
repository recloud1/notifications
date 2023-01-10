import asyncio
import typing
from typing import Callable
from uuid import uuid4

import pytest
from endpoints.utils.containers import run_alembic_migrations
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.testclient import TestClient
from testcontainers.postgres import PostgresContainer

from dependencies.auth import user_authorized
from main import app
from schemas.auth import UserInfo
from utils.db_session import async_session_factory, get_db_session

USER_ID = uuid4()


def user_authorized_override() -> UserInfo:
    return UserInfo(id=USER_ID)


@pytest.fixture
def raw_database_fixture() -> Callable[[], typing.AsyncContextManager[AsyncSession]]:
    container = PostgresContainer()
    try:
        container.start()

        sync_connection_url = container.get_connection_url()
        current_async_connection_url = sync_connection_url.replace(
            "psycopg2", "asyncpg"
        )

        session, session_manager, _ = async_session_factory(
            current_async_connection_url
        )
        run_alembic_migrations(container)
        session.container = container

        yield session
    except Exception as e:
        try:
            container.stop(force=True, delete_volume=True)
        except Exception:
            raise ConnectionError("Failed to create postgres container") from e


@pytest.fixture
def app_fixture(raw_database_fixture) -> TestClient:
    client = TestClient(app, base_url="http://localhost")

    app.dependency_overrides[get_db_session] = raw_database_fixture
    app.dependency_overrides[user_authorized] = user_authorized_override
    client.session = raw_database_fixture

    yield client


@pytest.fixture
def event_loop():
    return asyncio.get_event_loop()
