from sqlalchemy import text

import otm_workbench.models  # noqa: F401
from otm_workbench.database import Base, session_scope


def test_database_session_executes_sql():
    with session_scope() as session:
        result = session.execute(text("select 1")).scalar_one()

    assert result == 1


def test_metadata_contains_foundation_tables():
    table_names = set(Base.metadata.tables)

    assert "users" in table_names
    assert "workspaces" in table_names
    assert "modules" in table_names
