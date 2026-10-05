"""SQLite engine, sessions and the schema version check."""

import logging
from collections.abc import Generator

from sqlalchemy import Engine, create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

logger = logging.getLogger("croprisk")

# Bump this whenever a model changes. Old databases are not migrated: start.sh --reset.
SCHEMA_VERSION = 3


def make_engine(url: str) -> Engine:
    new_engine = create_engine(url, connect_args={"check_same_thread": False})

    @event.listens_for(new_engine, "connect")
    def set_sqlite_pragmas(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return new_engine


engine = make_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(engine_obj: Engine) -> None:
    """Create the tables on an empty database, or refuse to start on an old one."""
    with engine_obj.begin() as conn:
        version = conn.execute(text("PRAGMA user_version")).scalar()
        if version == SCHEMA_VERSION:
            return

        table_count = conn.execute(
            text("SELECT count(*) FROM sqlite_master WHERE type='table'")
        ).scalar()
        if version != 0 or table_count:
            raise RuntimeError(
                f"schema v{version} found, expected {SCHEMA_VERSION}: run ./scripts/start.sh --reset"
            )

        Base.metadata.create_all(conn)
        conn.execute(text(f"PRAGMA user_version = {SCHEMA_VERSION}"))
        logger.info("Created a new database at schema v%s.", SCHEMA_VERSION)
