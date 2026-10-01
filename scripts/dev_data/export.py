"""Export a subset of production data for a local development environment

Ported from the private MuckRock/dev_env_data repo.  A JSON config lists table
walk commands; each command exports rows to a CSV, and the run ends by writing
a psql script that loads every CSV.

The original tool loads into a fresh install.  This port adds:

- PK: tables whose primary key is not `id` (multi-table inheritance children)
- BACK with an optional extra SQL condition
- CLEAN_FIELD with an optional replacement value
- REDACT_WHERE: overwrite a field only on rows matching a condition in prod
- DEFINE: named SQL snippets, substituted into conditions as {{name}}
- --upsert: load additively into an existing database, skipping rows that
  already exist and bumping sequences afterwards

Run on the host, not in docker (it needs the Heroku CLI):

    uv run --no-project --with psycopg2-binary scripts/dev_data/export.py \\
        muckrock scripts/dev_data/review_agency_head.json \\
        --out fixtures-prod/review_agency_head \\
        --container-dir /app/fixtures-prod/review_agency_head --upsert
"""

# Standard Library
import argparse
import csv
import json
import os
import subprocess
import sys

# Third Party
import psycopg2
from psycopg2.sql import SQL, Identifier, Literal

NULL = "-NULL-"

# Loads a staging table into its target, using only the columns both have.
# Production can be ahead of a local branch's migrations; a column the local
# table lacks is skipped with a notice rather than failing the load.  Staging
# columns are text, cast to the target column's type.
#
# Two steps.  With `refresh`, rows whose primary key already exists locally
# are first updated to the production values where they differ -- otherwise a
# row from an earlier import keeps its stale state (an address that has since
# started bouncing still reads "good").  Then rows with new primary keys are
# inserted, skipping any that collide on another unique key, such as an M2M
# pair already present under a different id.
UPSERT_FUNCTION = """\
CREATE FUNCTION pg_temp.upsert_shared_columns(
    target text, stage text, csv_cols text[], pk text, refresh boolean
)
RETURNS TABLE (loaded_table text, staged bigint, inserted bigint, updated bigint) AS $$
DECLARE
    cols text;
    casts text;
    set_cols text;
    set_casts text;
    current_cols text;
    pk_type text;
    skipped text;
BEGIN
    SELECT string_agg(quote_ident(a.attname), ',' ORDER BY a.attnum),
           string_agg(
               format('s.%I::%s', a.attname, format_type(a.atttypid, a.atttypmod)),
               ',' ORDER BY a.attnum
           ),
           string_agg(quote_ident(a.attname), ',' ORDER BY a.attnum)
               FILTER (WHERE a.attname <> pk),
           string_agg(
               format('s.%I::%s', a.attname, format_type(a.atttypid, a.atttypmod)),
               ',' ORDER BY a.attnum
           ) FILTER (WHERE a.attname <> pk),
           string_agg(format('t.%I', a.attname), ',' ORDER BY a.attnum)
               FILTER (WHERE a.attname <> pk),
           max(format_type(a.atttypid, a.atttypmod)) FILTER (WHERE a.attname = pk)
      INTO cols, casts, set_cols, set_casts, current_cols, pk_type
      FROM pg_attribute a
     WHERE a.attrelid = target::regclass
       AND a.attnum > 0
       AND NOT a.attisdropped
       AND a.attname = ANY (csv_cols);
    SELECT string_agg(c, ', ') INTO skipped
      FROM unnest(csv_cols) c
     WHERE NOT EXISTS (
         SELECT 1 FROM pg_attribute a
          WHERE a.attrelid = target::regclass
            AND a.attname = c
            AND a.attnum > 0
            AND NOT a.attisdropped
     );
    IF skipped IS NOT NULL THEN
        RAISE NOTICE '%: skipping columns missing locally: %', target, skipped;
    END IF;
    loaded_table := target;
    updated := 0;
    EXECUTE format('SELECT count(*) FROM %I', stage) INTO staged;
    IF refresh AND set_cols IS NOT NULL THEN
        EXECUTE format(
            'UPDATE %I t SET (%s) = ROW(%s) FROM %I s '
            'WHERE t.%I = s.%I::%s AND ROW(%s) IS DISTINCT FROM ROW(%s)',
            target, set_cols, set_casts, stage,
            pk, pk, pk_type, current_cols, set_casts
        );
        GET DIAGNOSTICS updated = ROW_COUNT;
    END IF;
    EXECUTE format(
        'INSERT INTO %I (%s) SELECT %s FROM %I s '
        'WHERE NOT EXISTS (SELECT 1 FROM %I t WHERE t.%I = s.%I::%s) '
        'ON CONFLICT DO NOTHING',
        target, cols, casts, stage, target, pk, pk, pk_type
    );
    GET DIAGNOSTICS inserted = ROW_COUNT;
    RETURN NEXT;
END
$$ LANGUAGE plpgsql;
"""

# Values larger than the csv module's default limit do occur in communications
csv.field_size_limit(sys.maxsize)


def get_conn_str(name, out_dir):
    """Use the Heroku CLI to get the DB connection information

    The connection string is cached in the output directory, which must be
    gitignored -- it is a production credential.
    """
    path = os.path.join(out_dir, f"{name}.conn_str")
    if os.path.exists(path):
        with open(path) as file:
            return file.read()

    print("Fetching credentials...")
    # capture stdout only: stderr stays on the terminal, so a login prompt
    # from the Heroku CLI is visible rather than silently waiting for input
    result = subprocess.run(
        ["heroku", "pg:credentials:url", "-a", name],
        stdout=subprocess.PIPE,
        text=True,
        check=True,
    )
    # find first two quotes and grab that quoted string
    start = result.stdout.find('"')
    end = result.stdout.find('"', start + 1)
    conn_str = result.stdout[start + 1 : end]
    with open(path, "w") as file:
        file.write(conn_str)
    os.chmod(path, 0o600)
    return conn_str


class Exporter:
    """Runs a list of table walk commands against a database cursor"""

    def __init__(self, cur, out_dir=".", container_dir=None):
        self.cur = cur
        self.out_dir = str(out_dir)
        # where psql will find the CSVs; relative names if not given, which
        # matches the original tool's `\cd data` workflow
        self.container_dir = container_dir
        self.ids = {}
        self.pks = {}
        # tables whose existing local rows are kept rather than refreshed
        self.keep_local = set()
        self.defines = {}
        # tables exported more than once, in order to clean out duplicates
        self.clean_tables = []
        self.clear_tables = []

    # helpers

    def pk(self, table):
        return self.pks.get(table, "id")

    def set_pk(self, table, pk):
        self.pks[table] = pk

    def define(self, name, sql):
        self.defines[name] = self.expand(sql)

    def expand(self, sql):
        """Substitute {{name}} snippets into a SQL condition"""
        for name, value in self.defines.items():
            sql = sql.replace("{{%s}}" % name, value)
        return sql

    def path(self, table):
        return os.path.join(self.out_dir, f"{table}.csv")

    def read_rows(self, table):
        with open(self.path(table), newline="") as file:
            return list(csv.DictReader(file))

    def write_rows(self, table, rows):
        with open(self.path(table), "w", newline="") as file:
            csv_writer = csv.DictWriter(file, fieldnames=rows[0].keys())
            csv_writer.writeheader()
            csv_writer.writerows(rows)

    def read_data(self, table, field):
        return [r[field] for r in self.read_rows(table) if r[field] and r[field] != NULL]

    # CSV post-processing

    def clean_data(self, table):
        """Remove duplicates"""
        pk = self.pk(table)
        seen = set()
        rows = []
        for row in self.read_rows(table):
            if row[pk] not in seen:
                rows.append(row)
                seen.add(row[pk])
        self.write_rows(table, rows)

    def clean_key(self, from_table, field, to_table):
        """Set a FK to null if it doesn't exist in the data set"""
        if os.path.exists(self.path(to_table)):
            ids = set(self.read_data(to_table, self.pk(to_table)))
        else:
            ids = set()
        if not os.path.exists(self.path(from_table)):
            return
        rows = self.read_rows(from_table)
        for row in rows:
            if row[field] not in ids:
                row[field] = NULL
        if rows:
            self.write_rows(from_table, rows)

    def clean_field(self, table, field, value=""):
        """Clear out a field, such as sensitive information, in a table"""
        if not os.path.exists(self.path(table)):
            return
        rows = self.read_rows(table)
        for row in rows:
            row[field] = value
        if rows:
            self.write_rows(table, rows)

    def redact_where(self, table, field, condition, value=""):
        """Overwrite a field on exported rows which match a condition in prod

        `value` may contain {pk}, for fields which must stay unique.
        """
        if not os.path.exists(self.path(table)):
            return
        rows = self.read_rows(table)
        if not rows:
            return
        pk = self.pk(table)
        sql = SQL("select {pk} from {table} where {pk} in {ids} and ({condition})").format(
            pk=Identifier(pk),
            table=Identifier(table),
            ids=Literal(tuple(sorted({r[pk] for r in rows}))),
            condition=SQL(self.expand(condition)),
        )
        self.cur.execute(sql)
        matches = {str(r[0]) for r in self.cur.fetchall()}
        for row in rows:
            if row[pk] in matches:
                row[field] = value.replace("{pk}", row[pk])
        self.write_rows(table, rows)
        print(f"Redacted {table}.{field} on {len(matches):,d} rows")

    # exporting

    def export_data(self, table, condition):
        # if the CSV file exists, we want to append to it
        # that means we do not want headers, and we open the file
        # in append mode instead of write mode
        if os.path.exists(self.path(table)):
            header = ""
            mode = "a"
            self.clean_tables.append(table)
        else:
            header = "header"
            mode = "w"

        sql = SQL(
            """
            copy (
                select *
                from {table}
                where {condition}
                order by {pk}
            ) to stdout with csv null '-NULL-' {header}
        """
        ).format(
            table=Identifier(table),
            condition=condition,
            pk=Identifier(self.pk(table)),
            header=SQL(header),
        )

        with open(self.path(table), mode) as file:
            self.cur.copy_expert(sql, file)

        ids = self.read_data(table, self.pk(table))
        print(f"Exported {len(ids):,d} rows from {table}")
        return ids

    def export_all(self, table):
        sql = SQL("copy {table} to stdout with csv null '-NULL-' header").format(
            table=Identifier(table)
        )
        with open(self.path(table), "w") as file:
            self.cur.copy_expert(sql, file)

        ids = self.read_data(table, self.pk(table))
        print(f"Exported {len(ids):,d} rows from {table}")
        return ids

    def export_data_by_ids(self, table, id_field, ids, extra=None):
        if not ids:
            print(f"Exported 0 rows from {table} (no ids to follow)")
            return self.ids.get(table, [])

        condition = SQL("{id_field} in {ids}").format(
            id_field=Identifier(id_field),
            ids=Literal(tuple(sorted(set(ids)))),
        )
        if extra:
            condition = SQL("{condition} and ({extra})").format(
                condition=condition, extra=SQL(self.expand(extra))
            )
        return self.export_data(table, condition)

    def run(self, commands):
        for command, args in commands:
            if command == "BACK":
                # Pick rows of a table which has a foreign key which points BACK to
                # an already imported table, optionally narrowed by a condition
                table, field, id_table, *extra = args
                self.ids[table] = self.export_data_by_ids(
                    table, field, self.ids.get(id_table, []), *extra
                )
            elif command == "FORE":
                # Pick rows of a table which is pointed FOREward to by an already
                # imported table
                from_table, field, to_table = args
                if os.path.exists(self.path(from_table)):
                    temp_ids = self.read_data(from_table, field)
                else:
                    temp_ids = []
                self.ids[to_table] = self.export_data_by_ids(
                    to_table, self.pk(to_table), temp_ids
                )
            elif command == "ALL":
                # Export the entire table
                (table,) = args
                self.ids[table] = self.export_all(table)
            elif command == "SQL":
                # Custom condition
                table, sql = args
                self.ids[table] = self.export_data(table, SQL(self.expand(sql)))
            elif command == "PK":
                self.set_pk(*args)
            elif command == "DEFINE":
                self.define(*args)
            elif command == "KEEP_LOCAL":
                self.keep_local.add(*args)
            elif command == "CLEAN_KEY":
                self.clean_key(*args)
            elif command == "CLEAN_FIELD":
                self.clean_field(*args)
            elif command == "REDACT_WHERE":
                self.redact_where(*args)
            elif command == "CLEAR":
                (table,) = args
                self.clear_tables.append(table)
            else:
                raise ValueError(f"Unknown command: {command}")

        for table in self.clean_tables:
            self.clean_data(table)

    def plan(self, commands):
        """Register the tables a config exports, in order, without querying

        For --sql-only: rebuilds import.sql from CSVs already on disk.
        """
        for command, args in commands:
            if command == "PK":
                self.set_pk(*args)
            elif command == "KEEP_LOCAL":
                self.keep_local.add(*args)
            elif command in ("SQL", "ALL", "BACK"):
                self.ids.setdefault(args[0], [])
            elif command == "FORE":
                self.ids.setdefault(args[2], [])

    # SQL generation

    def csv_ref(self, table):
        if self.container_dir:
            return f"{self.container_dir.rstrip('/')}/{table}.csv"
        return f"{table}.csv"

    def generate_sql(self, upsert=False):
        lines = ["BEGIN;", "SET CONSTRAINTS ALL DEFERRED;", ""]
        if upsert:
            lines.append(UPSERT_FUNCTION)
        else:
            for table in self.clear_tables:
                lines.append(f"DELETE FROM {table};")
        copy_opts = "WITH (FORMAT CSV, NULL '-NULL-', HEADER)"
        tables = [t for t in self.ids if os.path.exists(self.path(t))]
        for table in tables:
            with open(self.path(table), newline="") as file:
                header = next(csv.reader(file))
            cols = ",".join(f'"{col}"' for col in header)
            if not upsert:
                lines.append(
                    f"\\copy {table} ({cols}) FROM '{self.csv_ref(table)}' {copy_opts}"
                )
                continue
            # Stage as untyped text with no constraints: CSV columns the local
            # table lacks can still be copied (the helper skips them), and
            # local columns the CSV lacks get the target's defaults on insert.
            # Rows that already exist are skipped; staged minus inserted is
            # how many, which is worth reading -- a skipped row may be a local
            # row that happens to share a prod id.
            stage = f"stage_{table}"
            stage_cols = ",".join(f'"{col}" text' for col in header)
            csv_cols = ",".join(f"'{col}'" for col in header)
            lines += [
                f"CREATE TEMP TABLE {stage} ({stage_cols}) ON COMMIT DROP;",
                f"\\copy {stage} ({cols}) FROM '{self.csv_ref(table)}' {copy_opts}",
                f"SELECT * FROM pg_temp.upsert_shared_columns"
                f"('{table}', '{stage}', ARRAY[{csv_cols}], '{self.pk(table)}', "
                f"{'false' if table in self.keep_local else 'true'});",
                "",
            ]
        if upsert:
            # rows arrived with explicit ids; move sequences past them
            for table in tables:
                pk = self.pk(table)
                if pk == "id":
                    lines.append(
                        f"SELECT setval(pg_get_serial_sequence('{table}', '{pk}'), "
                        f'max("{pk}")) FROM {table};'
                    )
        lines += ["", "COMMIT;", ""]
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("app", help="Heroku app name, e.g. muckrock")
    parser.add_argument("config", help="JSON file of table walk commands")
    parser.add_argument("--out", default=".", help="directory for CSVs and SQL")
    parser.add_argument(
        "--container-dir",
        help="path to --out as psql will see it, e.g. /app/fixtures-prod/...",
    )
    parser.add_argument(
        "--upsert",
        action="store_true",
        help="load additively into an existing database",
    )
    parser.add_argument(
        "--sql-only",
        action="store_true",
        help="rebuild import.sql from the CSVs already in --out, without exporting",
    )
    args = parser.parse_args()

    with open(args.config) as file:
        commands = json.load(file)

    if args.sql_only:
        exporter = Exporter(None, args.out, args.container_dir)
        exporter.plan(commands)
    else:
        os.makedirs(args.out, exist_ok=True)
        stale = [f for f in os.listdir(args.out) if f.endswith(".csv")]
        if stale:
            sys.exit(f"{args.out} already has CSVs; clear them first (exports append)")

        conn = psycopg2.connect(get_conn_str(args.app, args.out))
        # never write to production
        conn.set_session(readonly=True)
        print("Connection established!")

        exporter = Exporter(conn.cursor(), args.out, args.container_dir)
        exporter.run(commands)

    sql_path = os.path.join(args.out, "import.sql")
    with open(sql_path, "w") as sql_file:
        sql_file.write(exporter.generate_sql(upsert=args.upsert))
    print(f"Wrote {sql_path}")


if __name__ == "__main__":
    main()
