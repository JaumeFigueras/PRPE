#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tempfile

from pytest_postgresql import factories
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import NullPool
from sqlalchemy import text
from src.data_model import Base
import pytest


test_folder: Path = Path(__file__).parent
socket_dir: tempfile.TemporaryDirectory = tempfile.TemporaryDirectory()
postgresql_proc_prpe = factories.postgresql_proc(port=None, unixsocketdir=socket_dir.name, dbname='test_db')
postgresql_prpe = factories.postgresql('postgresql_proc_prpe')

@pytest.fixture(scope='function')
def db_session(postgresql_prpe):
    """Session for SQLAlchemy."""
    connection = f'postgresql+psycopg://{postgresql_prpe.info.user}:@{postgresql_prpe.info.host}:{postgresql_prpe.info.port}/{postgresql_prpe.info.dbname}'
    engine = create_engine(connection, echo=False, poolclass=NullPool)
    session = scoped_session(sessionmaker(bind=engine))

    sql_filename = str(test_folder) + '/database_init.sql'
    with open(sql_filename, 'r') as sql_file:
        sql = text(sql_file.read())
        session.execute(sql)

    Base.metadata.create_all(engine)

    yield session

    Base.metadata.drop_all(engine)
    session.commit()

"""
Configuration of the database.

The setup creates a temporary database with the full schema but without any data that will be added as necessary in the 
fixtures. Uses a initialization file to simulate the real users: 'richal_user' and 'richal_remoteuser' and then the 
SQL files stored in the data model
"""



pytest_plugins = [
    'test.fixtures.database',
]

"""
Configuration of the fixtures.

Sets up the fixtures for the database population, FMP API responses
"""