"""
Migration safety checks, each on its own throwaway database.

The important one is the upgrade path for Luke's existing database:
it already has weight_entries/weight_goals (created by the original
code's Base.metadata.create_all) but no alembic_version table.
"""

import datetime
import os

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url

from alembic import command
from app.database import Base
from app.models.weight import WeightEntry
from app.models.weight_goal import WeightGoal
from tests.conftest import TEST_DATABASE_URL
from tests.helpers import alembic_config, create_database, drop_database

HEALTH_TABLES = {"weight_entries", "weight_goals"}
NEW_TABLES = {
    "money_accounts", "money_categories", "money_transactions", "money_budgets",
    "money_recurring_bills", "money_debts", "calendar_events", "tasks",
    "invest_holdings", "invest_watchlist", "job_applications", "job_interviews",
    "career_contacts", "career_certifications",
}


@pytest.fixture
def scratch_db():
    url = os.environ.get("MIGRATION_TEST_DATABASE_URL") or str(
        make_url(TEST_DATABASE_URL).set(
            database=make_url(TEST_DATABASE_URL).database + "_migrations"
        ).render_as_string(hide_password=False)
    )
    create_database(url)
    engine = create_engine(url)
    yield url, engine
    engine.dispose()
    drop_database(url)


def tables(engine) -> set[str]:
    return set(inspect(engine).get_table_names())


def schema_diff(engine):
    with engine.connect() as connection:
        context = MigrationContext.configure(connection, opts={"compare_type": True})
        return compare_metadata(context, Base.metadata)


def test_upgrade_head_on_empty_database(scratch_db):
    url, engine = scratch_db
    command.upgrade(alembic_config(url), "head")

    assert tables(engine) == HEALTH_TABLES | NEW_TABLES | {"alembic_version"}
    assert schema_diff(engine) == []  # migrations == models


def test_downgrade_and_upgrade_again(scratch_db):
    url, engine = scratch_db
    config = alembic_config(url)
    command.upgrade(config, "head")

    command.downgrade(config, "0001_health_tables")
    assert tables(engine) == HEALTH_TABLES | {"alembic_version"}

    command.downgrade(config, "base")
    assert tables(engine) == {"alembic_version"}

    command.upgrade(config, "head")
    assert NEW_TABLES <= tables(engine)


def test_stamp_then_upgrade_existing_health_database(scratch_db):
    url, engine = scratch_db

    # 1. What the ORIGINAL app did on startup (create_all of the 2 models)
    Base.metadata.create_all(
        engine, tables=[WeightEntry.__table__, WeightGoal.__table__]
    )
    with engine.begin() as connection:
        connection.execute(text(
            "INSERT INTO weight_entries (weight, measurement_date, created_at) "
            "VALUES (262.4, '2026-09-01', now()), (255.0, '2026-09-28', now())"
        ))
        connection.execute(text(
            "INSERT INTO weight_goals (starting_weight, goal_weight, status, created_at, "
            "activated_at) VALUES (262, 200, 'active', now(), now())"
        ))

    # 2. The first revision describes exactly these tables: nothing to change
    with engine.connect() as connection:
        context = MigrationContext.configure(connection, opts={"compare_type": True})
        health_diff = [
            d for d in compare_metadata(context, Base.metadata)
            if not (d[0] == "add_table" and d[1].name in NEW_TABLES)
            and not (d[0] == "add_index" and d[1].table.name in NEW_TABLES)
        ]
    assert health_diff == []

    # 3. Luke's upgrade steps
    config = alembic_config(url)
    command.stamp(config, "0001_health_tables")
    command.upgrade(config, "head")

    assert tables(engine) == HEALTH_TABLES | NEW_TABLES | {"alembic_version"}
    assert schema_diff(engine) == []

    with engine.connect() as connection:
        weights = connection.execute(
            text("SELECT weight FROM weight_entries ORDER BY id")
        ).scalars().all()
        version = connection.execute(text("SELECT version_num FROM alembic_version")).scalar()
    assert weights == [262.4, 255.0]
    assert version == "0002_lifeops_modules"

    # New rows still get fresh ids (sequences intact)
    with engine.begin() as connection:
        new_id = connection.execute(text(
            "INSERT INTO weight_entries (weight, measurement_date, created_at) "
            "VALUES (250, :day, now()) RETURNING id"
        ), {"day": datetime.date(2026, 10, 1)}).scalar()
    assert new_id == 3
