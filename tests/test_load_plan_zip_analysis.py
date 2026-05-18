from sqlalchemy import inspect

from otm_workbench.database import engine


def test_load_plan_zip_analyses_table_exists_after_metadata_reset():
    tables = set(inspect(engine).get_table_names())

    assert "load_plan_zip_analyses" in tables
