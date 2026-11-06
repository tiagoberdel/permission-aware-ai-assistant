import pytest

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.db import Base

import app.models

@pytest.fixture(scope="session")
def test_engine():
    test_url = make_url(settings.DATABASE_URL).set(
        database="andino_test"
    )

    if test_url.database != "andino_test":
        raise RuntimeError("La base de testing no es andino_test")

    engine = create_engine(test_url)

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    yield engine

    Base.metadata.drop_all(engine)
    engine.dispose()

@pytest.fixture
def db_session(test_engine):
    connection = test_engine.connect()
    transaction = connection.begin()

    TestingSessionLocal = sessionmaker(
        bind=connection,
        autoflush=False,
        join_transaction_mode="create_savepoint"
    )

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()