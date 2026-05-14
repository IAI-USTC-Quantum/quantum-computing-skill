# Task DB schema and migration

uniqc keeps the local task cache in a single SQLite file at
`~/.uniqc/cache/tasks.sqlite`. The schema version is checked at every
process start and migrated lazily.

## Current schema (uniqc 0.0.12+)

```
tasks               primary task table; columns include id (TEXT),
                    status, platform, backend, shots, submit_time,
                    metadata (JSON), result (JSON), error_message
task_shards         maps each uqt_* parent to one or more
                    platform-issued ids; ON DELETE CASCADE from tasks
archived_tasks      same shape as tasks; archived rows go here
archived_task_shards same shape as task_shards
```

Schema version bumps:

| From | To | When                                 | What changes                                                    |
| ---: | -: | ------------------------------------ | --------------------------------------------------------------- |
|    2 |  4 | uniqc 0.0.12 first run               | Adds `task_shards` + `archived_task_shards` (ON DELETE CASCADE) |
|    4 |  5 | uniqc 0.0.12 first run on legacy rows | Each old `tasks` row gets a synthetic `uqt_*` parent + 1 shard with `metadata.legacy_platform_id` preserved |

The migration is **automatic** and **idempotent** — running uniqc on
an old DB just bumps it on first read.

## Doctor's "Task DB" section

```
schema_version: 5      ✓ current
rows: 47               ✓
oldest_pending: ...    (or "none")
unmigrated_rows: 0     ✓
```

If `schema_version` is `< 5` or `unmigrated_rows > 0`, run any
`uniqc task list` command — that triggers the migration.

## Inspecting tasks

```bash
uniqc task list                          # all
uniqc task list --platform originq       # filter
uniqc task list --status running         # filter
uniqc task list --limit 20 --offset 0    # pagination (uniqc 0.0.13 threads --limit/--offset to SQLite)
uniqc task show <uqt_*>                  # single-row detail
uniqc task shards <uqt_*>                # platform task id mapping
```

## Resetting the DB

The DB is safe to delete; you only lose the local mirror of remote
task results. Real cloud results stay on the platform.

```bash
mv ~/.uniqc/cache/tasks.sqlite ~/.uniqc/cache/tasks.sqlite.bak
```

Next uniqc invocation will create a fresh schema-5 DB.

## Known issues

- **Pre-0.0.12 DBs that pre-date the `uqt_*` indirection layer** carry
  raw platform ids. The migration creates `uqt_*` parents for them;
  `query_task(<old_platform_id>)` still works but emits
  `DeprecationWarning`.
- **Archive round-trip** — uniqc 0.0.12 fixed a bug where
  `ArchiveStore.restore_task` iterated a `sqlite3.Row` as values
  instead of keys, raising `IndexError`. If you see that on an old
  uniqc, upgrade.
- **Multiple processes writing concurrently** — SQLite is fine for
  read-heavy workloads but `uniqc submit` from many shells at once
  can occasionally hit the default 5-second busy timeout. Serialize
  or lengthen the timeout (`PRAGMA busy_timeout`).
