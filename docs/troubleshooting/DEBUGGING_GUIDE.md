# Debugging Guide

For running from source. Commands assume the project root and the project's
environment (`venv/bin/python`; on Windows `venv\Scripts\python`).

## Logs

The app logs to the terminal and to `logs/app.log` inside your data folder
(the folder named by `HEALTH_LEDGER_DATA_DIR`). Each line has the time, logger
name, level, `file:line` and message.

```bash
tail -f "<data folder>/logs/app.log"
grep ERROR "<data folder>/logs/app.log"
```

The level is INFO. To get DEBUG lines, set `HEALTH_LEDGER_DEBUG=1` (also
`true`, `yes` or `on`) in the environment or in the `.env` file. That flag also
turns on Flask's debug mode, which serves an interactive debugger to anything
that can reach the port. Use it only on your own machine, and unset it
afterwards.

## The database

The file is `genetic_profile.db` in your data folder, unless
`HEALTH_LEDGER_DB_PATH` names another. Look at it with the `sqlite3` command
line tool or any SQLite browser:

```bash
sqlite3 "<data folder>/genetic_profile.db" ".tables"
sqlite3 "<data folder>/genetic_profile.db" "PRAGMA integrity_check;"
```

The tables are defined in `genetic_profile_db_schema.sql`.

From Python, the same connection the app uses:

```bash
venv/bin/python -c "
from database_manager import GeneticProfileDB
db = GeneticProfileDB()
print(len(db.get_all_genes()), 'genes')
db.close()
"
```

Work on a copy of the file, or take a backup first, if you are going to write
to it.

## The API

With the app running, each of these returns JSON:

```bash
curl http://127.0.0.1:5001/test
curl http://127.0.0.1:5001/api/all-genes
curl http://127.0.0.1:5001/api/all-conditions
curl http://127.0.0.1:5001/api/all-traits
curl "http://127.0.0.1:5001/api/genes-by-condition?condition=asthma"
curl "http://127.0.0.1:5001/api/gene-info?gene=CYP2D6"
curl http://127.0.0.1:5001/api/sources
curl http://127.0.0.1:5001/api/references
```

The conditions and genes in your ledger will differ; `/api/all-conditions` and
`/api/all-genes` list the real names. Every route, with its parameters, is in
[API_REFERENCE.md](../api/API_REFERENCE.md). Most routes log an error, with its
traceback, to `logs/app.log` before returning a 500.

## Templates

A page that fails to render returns a short "Error loading ..." message, and
the cause is in the log. The templates are in `templates/`; most extend
`base.html`.

## The browser side

See [DEBUGGING_JAVASCRIPT.md](DEBUGGING_JAVASCRIPT.md). After editing any
`static/js/*.ts` file, run `npm run build`, because the browser loads the
compiled `.js` next to it.

## Tests

```bash
venv/bin/python -m pytest
```

`tests/README.md` says what each group covers. `npm run check` runs the lint
and the type check for the front end.

## Stopping at a line

Put `breakpoint()` in the Python where you want to stop and run
`venv/bin/python app.py` from a terminal.
