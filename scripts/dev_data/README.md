# Production data subsets for local development

`export.py` is ported from the private
[MuckRock/dev_env_data](https://github.com/MuckRock/dev_env_data) repo. A JSON config lists table-walk commands. The script runs them against the production database, writing CSVs and a psql script that loads them.

| Config | What it loads |
|---|---|
| `review_agency_head.json` | The top 30 agencies by blocked requests: open requests routed at an error-status email address, at agencies that have an open `ReviewAgencyTask`. It brings each agency's full channel roster, its review agency tasks (open, or resolved within 24 months), every open request, and 24 months of communications with their email errors and opens. See `review_agency_task_design.md` §9. |

## Commands

The original commands are `BACK`, `FORE`, `ALL`, `SQL`, `CLEAN_KEY`, `CLEAN_FIELD` and `CLEAR`. This port adds these:

| Command | Args | Meaning |
|---|---|---|
| `PK` | table, column | The table's primary key isn't `id`. This applies to multi-table inheritance children like `task_reviewagencytask`. |
| `DEFINE` | name, sql | A named SQL snippet. Use it in later conditions as `{{name}}`. |
| `BACK` | table, fk, id_table, *[condition]* | The optional condition is ANDed onto the id filter. |
| `CLEAN_FIELD` | table, field, *[value]* | Overwrites the field with `value` instead of blanking it. |
| `KEEP_LOCAL` | table | In an upsert load, leaves this table's existing local rows alone instead of refreshing them. |
| `REDACT_WHERE` | table, field, condition, value | Overwrites the field only on exported rows that match `condition` in prod. `value` may contain `{pk}` for fields that must stay unique. |

## Loading the review agency head

This load is **additive**. It keeps your current local database and runs in two steps. First, a row whose id already exists locally is **updated to the production values** where they differ, so a row from an earlier import doesn't keep stale state (an address that has since started bouncing would still read `good`). Then rows with new ids are inserted, skipping any that collide on another unique key. Tables marked `KEEP_LOCAL` (users, profiles, organizations) are never updated, so your local staff accounts aren't overwritten with redacted copies. Sequences are moved past the imported ids afterwards.

1. **Snapshot** the local database, so the load and anything you rehearse on it can be rolled back:

   ```bash
   docker compose -f local.yml exec muckrock_postgres backup
   docker compose -f local.yml exec muckrock_postgres backups   # list them
   ```

2. **Export from production** on the host. You need the Heroku CLI, logged in with access to the `muckrock` app. The connection is opened read-only.

   ```bash
   uv run --no-project --with psycopg2-binary scripts/dev_data/export.py \
       muckrock scripts/dev_data/review_agency_head.json \
       --out fixtures-prod/review_agency_head \
       --container-dir /app/fixtures-prod/review_agency_head \
       --upsert
   ```

   To rebuild `import.sql` from CSVs you already exported, without touching production, add `--sql-only`.

   `fixtures-prod/` is gitignored. It also holds the cached `muckrock.conn_str`, which is a production credential. Exports append to existing CSVs, so the script refuses to run if the output directory already has any. Delete them before exporting again.

3. **Import** into the local database:

   ```bash
   inv dbshell --opts="-- -v ON_ERROR_STOP=1 -q -f /app/fixtures-prod/review_agency_head/import.sql"
   ```

   If production has columns your local schema doesn't (its migrations are ahead of your branch), those columns are skipped with a `NOTICE` naming them, and the rest of the row loads.

   Each table prints `staged`, `inserted` (new ids) and `updated` (existing rows that differed from prod). Staged rows in neither column were already current, or were new ids skipped on a unique collision.

4. **Snapshot again.** This pre-merge state is the baseline for rehearsing:

   ```bash
   inv manage -c "merge_email_addresses --dry-run"
   inv manage -c "split_review_agency_tasks --dry-run"
   ```

   Restore with `docker compose -f local.yml exec muckrock_postgres restore <backup file>`.

## Redaction

Non-embargoed request content is already public at `/foi/*`, so it's left as is. Agency contacts, SMTP output and task rows are also left alone.

- **Always:** user email and password (set unusable), plus profile postal address and phone. Also request portal passwords and access keys, private from/to on communications, and organization cards.
- **Embargoed requests only** (expired embargoes count as public):
  - request and composer titles, slugs and bodies
  - communication bodies, subjects and from/to
  - the requester's names and username, their individual organization's name, and the display name on their request email addresses

## Tests

```bash
cd scripts/dev_data
uv run --no-project --with pytest --with psycopg2-binary pytest
```
