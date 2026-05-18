from otm_workbench.database import Base


def test_reference_catalog_tables_are_registered():
    table_names = set(Base.metadata.tables)

    assert "reference_object_types" in table_names
    assert "reference_objects" in table_names
    assert "reference_field_policies" in table_names
    assert "reference_import_batches" in table_names
    assert "otm_table_definitions" in table_names
    assert "otm_table_columns" in table_names
    assert "otm_table_foreign_keys" in table_names
    assert "otm_load_sequences" in table_names
    assert "otm_csv_contracts" in table_names
