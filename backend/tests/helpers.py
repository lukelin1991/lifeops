from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from alembic import command

BACKEND_DIR = __import__("pathlib").Path(__file__).resolve().parents[1]


def _admin_engine(database_url: str):
    """Engine connected to the 'postgres' maintenance database."""
    url = make_url(database_url).set(database="postgres")
    return create_engine(url, isolation_level="AUTOCOMMIT")


def create_database(database_url: str) -> None:
    name = make_url(database_url).database
    engine = _admin_engine(database_url)
    with engine.connect() as connection:
        connection.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
        connection.execute(text(f'CREATE DATABASE "{name}"'))
    engine.dispose()


def drop_database(database_url: str) -> None:
    name = make_url(database_url).database
    engine = _admin_engine(database_url)
    with engine.connect() as connection:
        connection.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
    engine.dispose()


def alembic_config(database_url: str) -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    return config


def run_migrations(database_url: str, revision: str = "head") -> None:
    command.upgrade(alembic_config(database_url), revision)
