"""Tests for the production subset exporter

These cover the parts that do not need a database: CSV post-processing and
SQL generation.  The one query-backed step, REDACT_WHERE, runs against a stub
cursor.

    uv run --with pytest --with psycopg2-binary pytest scripts/dev_data/test_export.py
"""

# Standard Library
import csv

# Third Party
import pytest

# Local
from export import Exporter


class StubCursor:
    """Records executed statements and returns canned rows"""

    def __init__(self, rows=()):
        self.rows = list(rows)
        self.executed = []

    def execute(self, sql):
        self.executed.append(sql)

    def fetchall(self):
        return self.rows


def write_csv(path, rows):
    with open(path, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path):
    with open(path, newline="") as file:
        return list(csv.DictReader(file))


@pytest.fixture
def exporter(tmp_path):
    return Exporter(StubCursor(), out_dir=tmp_path)


def test_pk_defaults_to_id(exporter):
    assert exporter.pk("agency_agency") == "id"
    exporter.set_pk("task_reviewagencytask", "task_ptr_id")
    assert exporter.pk("task_reviewagencytask") == "task_ptr_id"


def test_clean_data_dedupes_on_custom_pk(exporter, tmp_path):
    exporter.set_pk("task_reviewagencytask", "task_ptr_id")
    write_csv(
        tmp_path / "task_reviewagencytask.csv",
        [
            {"task_ptr_id": "1", "agency_id": "10"},
            {"task_ptr_id": "2", "agency_id": "10"},
            {"task_ptr_id": "1", "agency_id": "10"},
        ],
    )
    exporter.clean_data("task_reviewagencytask")
    rows = read_csv(tmp_path / "task_reviewagencytask.csv")
    assert [r["task_ptr_id"] for r in rows] == ["1", "2"]


def test_clean_key_nulls_missing_references(exporter, tmp_path):
    exporter.set_pk("task_reviewagencytask", "task_ptr_id")
    write_csv(tmp_path / "task_reviewagencytask.csv", [{"task_ptr_id": "5"}])
    write_csv(
        tmp_path / "task_note.csv",
        [{"id": "1", "task_id": "5"}, {"id": "2", "task_id": "6"}],
    )
    exporter.clean_key("task_note", "task_id", "task_reviewagencytask")
    rows = read_csv(tmp_path / "task_note.csv")
    assert [r["task_id"] for r in rows] == ["5", "-NULL-"]


def test_clean_field_with_value(exporter, tmp_path):
    write_csv(tmp_path / "auth_user.csv", [{"id": "1", "password": "secret"}])
    exporter.clean_field("auth_user", "password", "!")
    assert read_csv(tmp_path / "auth_user.csv")[0]["password"] == "!"


def test_redact_where_only_touches_matching_rows(tmp_path):
    cursor = StubCursor(rows=[(2,)])
    exporter = Exporter(cursor, out_dir=tmp_path)
    write_csv(
        tmp_path / "auth_user.csv",
        [
            {"id": "1", "username": "public-person"},
            {"id": "2", "username": "embargoed-person"},
        ],
    )
    exporter.redact_where("auth_user", "username", "is_staff = false", "embargoed-{pk}")
    rows = read_csv(tmp_path / "auth_user.csv")
    assert [r["username"] for r in rows] == ["public-person", "embargoed-2"]
    assert len(cursor.executed) == 1


def test_redact_where_skips_query_without_rows(exporter):
    exporter.redact_where("auth_user", "username", "true", "")
    assert exporter.cur.executed == []


def test_defines_substitute_into_conditions(exporter):
    exporter.define("embargoed", "embargo_status <> 'public'")
    assert (
        exporter.expand("id in (select id from t where {{embargoed}})")
        == "id in (select id from t where embargo_status <> 'public')"
    )


def test_fresh_sql_matches_original_format(exporter, tmp_path):
    write_csv(tmp_path / "agency_agency.csv", [{"id": "1", "name": "FBI"}])
    exporter.ids["agency_agency"] = ["1"]
    exporter.clear_tables.append("auth_user")
    sql = exporter.generate_sql(upsert=False)
    assert sql == (
        "BEGIN;\nSET CONSTRAINTS ALL DEFERRED;\n\n"
        "DELETE FROM auth_user;\n"
        "\\copy agency_agency (\"id\",\"name\") FROM 'agency_agency.csv' "
        "WITH (FORMAT CSV, NULL '-NULL-', HEADER)\n"
        "\nCOMMIT;\n"
    )


def test_upsert_sql_stages_and_skips_conflicts(tmp_path):
    exporter = Exporter(StubCursor(), out_dir=tmp_path, container_dir="/app/out")
    exporter.set_pk("task_reviewagencytask", "task_ptr_id")
    write_csv(tmp_path / "agency_agency.csv", [{"id": "1", "name": "FBI"}])
    write_csv(
        tmp_path / "task_reviewagencytask.csv",
        [{"task_ptr_id": "3", "agency_id": "1"}],
    )
    exporter.ids["agency_agency"] = ["1"]
    exporter.ids["task_reviewagencytask"] = ["3"]
    sql = exporter.generate_sql(upsert=True)

    assert "DELETE FROM" not in sql
    # staged as text, so CSV columns the local table lacks can still be copied
    assert (
        'CREATE TEMP TABLE stage_agency_agency ("id" text,"name" text) ON COMMIT DROP;'
    ) in sql
    assert (
        "\\copy stage_agency_agency (\"id\",\"name\") FROM "
        "'/app/out/agency_agency.csv' WITH (FORMAT CSV, NULL '-NULL-', HEADER)"
    ) in sql
    # the insert is built from the columns both sides have
    # existing rows are refreshed from prod unless the table is KEEP_LOCAL
    assert (
        "upsert_shared_columns('agency_agency', 'stage_agency_agency', "
        "ARRAY['id','name'], 'id', true)"
    ) in sql
    assert (
        "SELECT setval(pg_get_serial_sequence('agency_agency', 'id'), max(\"id\")) "
        "FROM agency_agency;"
    ) in sql
    # a multi-table-inheritance child has no sequence of its own
    assert "pg_get_serial_sequence('task_reviewagencytask'" not in sql
    assert sql.startswith("BEGIN;\nSET CONSTRAINTS ALL DEFERRED;\n")
    assert sql.endswith("COMMIT;\n")


def test_sql_skips_tables_without_a_csv(exporter, tmp_path):
    write_csv(tmp_path / "agency_agency.csv", [{"id": "1"}])
    exporter.ids["agency_agency"] = ["1"]
    exporter.ids["foia_trackingnumber"] = []
    sql = exporter.generate_sql(upsert=True)
    assert "foia_trackingnumber" not in sql


def test_upsert_sql_defines_the_helper(exporter, tmp_path):
    write_csv(tmp_path / "agency_agency.csv", [{"id": "1"}])
    exporter.ids["agency_agency"] = ["1"]
    sql = exporter.generate_sql(upsert=True)
    assert "CREATE FUNCTION pg_temp.upsert_shared_columns" in sql
    assert "ON CONFLICT DO NOTHING" in sql
    assert "RAISE NOTICE" in sql


def test_keep_local_tables_skip_existing_rows(exporter, tmp_path):
    write_csv(tmp_path / "auth_user.csv", [{"id": "1", "username": "staff"}])
    exporter.ids["auth_user"] = ["1"]
    exporter.run([["KEEP_LOCAL", ["auth_user"]]])
    sql = exporter.generate_sql(upsert=True)
    assert (
        "upsert_shared_columns('auth_user', 'stage_auth_user', "
        "ARRAY['id','username'], 'id', false)"
    ) in sql


def test_skip_kept_drops_children_of_colliding_local_rows(exporter, tmp_path):
    """A prod user sharing a local user's id must not bring its memberships

    The local user is kept, so its prod memberships would attach to the wrong
    person -- and a second individual organization breaks login.
    """
    write_csv(tmp_path / "auth_user.csv", [{"id": "1", "username": "prod"}])
    write_csv(
        tmp_path / "organization_membership.csv",
        [{"id": "9", "user_id": "1", "organization_id": "5"}],
    )
    exporter.ids["auth_user"] = ["1"]
    exporter.ids["organization_membership"] = ["9"]
    exporter.run(
        [
            ["KEEP_LOCAL", ["auth_user"]],
            ["SKIP_KEPT", ["organization_membership", "user_id", "auth_user"]],
        ]
    )
    sql = exporter.generate_sql(upsert=True)

    record = (
        "CREATE TEMP TABLE kept_auth_user ON COMMIT DROP AS "
        'SELECT s."id" AS id FROM stage_auth_user s '
        'WHERE EXISTS (SELECT 1 FROM auth_user t WHERE t."id"::text = s."id");'
    )
    skip = (
        "WITH skipped AS (DELETE FROM stage_organization_membership "
        'WHERE "user_id" IN (SELECT id FROM kept_auth_user) RETURNING 1) '
        "SELECT 'organization_membership' AS kept_parent_table, "
        "count(*) AS skipped FROM skipped;"
    )
    # collisions are recorded before the parent load inserts new ids
    assert sql.index(record) < sql.index("upsert_shared_columns('auth_user'")
    # and children are dropped from staging before they load
    assert sql.index(skip) < sql.index("upsert_shared_columns('organization_membership'")


def test_skip_kept_match_column_spares_earlier_imports(exporter, tmp_path):
    """A user from an earlier import is the same person, not a collision"""
    write_csv(tmp_path / "auth_user.csv", [{"id": "1", "username": "prod"}])
    write_csv(tmp_path / "organization_membership.csv", [{"id": "9", "user_id": "1"}])
    exporter.ids["auth_user"] = ["1"]
    exporter.ids["organization_membership"] = ["9"]
    exporter.run(
        [["SKIP_KEPT", ["organization_membership", "user_id", "auth_user", "username"]]]
    )
    sql = exporter.generate_sql(upsert=True)
    assert (
        'WHERE t."id"::text = s."id" '
        'AND t."username"::text IS DISTINCT FROM s."username");'
    ) in sql


def test_skip_kept_requires_parent_loaded_first(exporter, tmp_path):
    write_csv(tmp_path / "organization_membership.csv", [{"id": "9", "user_id": "1"}])
    write_csv(tmp_path / "auth_user.csv", [{"id": "1"}])
    exporter.ids["organization_membership"] = ["9"]
    exporter.ids["auth_user"] = ["1"]
    exporter.plan(
        [
            ["KEEP_LOCAL", ["auth_user"]],
            ["SKIP_KEPT", ["organization_membership", "user_id", "auth_user"]],
        ]
    )
    with pytest.raises(ValueError, match="auth_user"):
        exporter.generate_sql(upsert=True)


def test_skip_kept_ignored_without_upsert(exporter, tmp_path):
    write_csv(tmp_path / "auth_user.csv", [{"id": "1"}])
    exporter.ids["auth_user"] = ["1"]
    exporter.run([["SKIP_KEPT", ["organization_membership", "user_id", "auth_user"]]])
    assert "kept_auth_user" not in exporter.generate_sql(upsert=False)


def test_upsert_helper_refreshes_then_inserts(exporter, tmp_path):
    """Existing ids are updated where they differ; only new ids are inserted

    Inserting with ON CONFLICT DO NOTHING (no target) keeps a new row that
    collides on some other unique key -- an M2M pair already present under a
    different id -- from failing the load, as it would under an upsert
    targeting the primary key.
    """
    write_csv(tmp_path / "agency_agency.csv", [{"id": "1"}])
    exporter.ids["agency_agency"] = ["1"]
    sql = exporter.generate_sql(upsert=True)
    assert "UPDATE %I t SET (%s) = ROW(%s) FROM %I s" in sql
    assert "IS DISTINCT FROM" in sql
    assert "WHERE NOT EXISTS (SELECT 1 FROM %I t WHERE t.%I = s.%I::%s)" in sql
    assert "ON CONFLICT DO NOTHING" in sql
    assert "ON CONFLICT (" not in sql


def test_plan_registers_tables_without_querying(tmp_path):
    """--sql-only rebuilds import.sql from existing CSVs, in export order"""
    cursor = StubCursor()
    exporter = Exporter(cursor, out_dir=tmp_path)
    for table in ["agency_agency", "task_reviewagencytask", "task_task"]:
        write_csv(tmp_path / f"{table}.csv", [{"id": "1", "task_ptr_id": "1"}])
    exporter.plan(
        [
            ["PK", ["task_reviewagencytask", "task_ptr_id"]],
            ["KEEP_LOCAL", ["task_task"]],
            ["SQL", ["agency_agency", "true"]],
            ["BACK", ["task_reviewagencytask", "agency_id", "agency_agency"]],
            ["FORE", ["task_reviewagencytask", "task_ptr_id", "task_task"]],
            ["FORE", ["task_task", "assigned_id", "agency_agency"]],
            ["REDACT_WHERE", ["agency_agency", "name", "true", ""]],
        ]
    )
    assert list(exporter.ids) == ["agency_agency", "task_reviewagencytask", "task_task"]
    assert exporter.pk("task_reviewagencytask") == "task_ptr_id"
    assert exporter.keep_local == {"task_task"}
    assert cursor.executed == []


class CopyCursor(StubCursor):
    """Answers COPY with a canned CSV per table"""

    def __init__(self, tables):
        super().__init__()
        self.tables = tables

    def copy_expert(self, sql, file):
        self.executed.append(sql)
        table = next(t for t in self.tables if f"Identifier('{t}')" in repr(sql))
        file.write(self.tables[table])


def test_back_applies_extra_condition(tmp_path):
    cursor = CopyCursor({"foia_foiarequest": "id,agency_id\n7,1\n"})
    exporter = Exporter(cursor, out_dir=tmp_path)
    exporter.ids["agency_agency"] = ["1"]
    exporter.define("open", "status in ('ack')")
    exporter.run([["BACK", ["foia_foiarequest", "agency_id", "agency_agency", "{{open}}"]]])
    assert exporter.ids["foia_foiarequest"] == ["7"]
    assert "status in ('ack')" in repr(cursor.executed[0])


def test_review_agency_head_config_is_well_formed():
    """Every command is known and every {{snippet}} resolves"""
    # Standard Library
    import json
    import os
    import re

    path = os.path.join(os.path.dirname(__file__), "review_agency_head.json")
    with open(path) as file:
        commands = json.load(file)
    known = {
        "BACK", "FORE", "ALL", "SQL", "PK", "DEFINE",
        "CLEAN_KEY", "CLEAN_FIELD", "REDACT_WHERE", "CLEAR", "KEEP_LOCAL",
        "SKIP_KEPT",
    }
    exporter = Exporter(StubCursor())
    for command, args in commands:
        assert command in known
        if command == "DEFINE":
            exporter.define(*args)
        for arg in args:
            assert not re.search(r"\{\{\w+\}\}", exporter.expand(arg)), arg
    assert "CLEAR" not in {command for command, _ in commands}


def test_upsert_function_is_bare_sql():
    """No stray escape characters ahead of the CREATE"""
    # Local
    from export import UPSERT_FUNCTION

    assert UPSERT_FUNCTION.startswith("CREATE FUNCTION pg_temp.upsert_shared_columns(")
