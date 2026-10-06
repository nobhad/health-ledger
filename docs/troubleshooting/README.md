# Troubleshooting

| Page | For |
| --- | --- |
| [COMMON_ISSUES.md](COMMON_ISSUES.md) | The app will not open, a port is busy, a file will not import, PDFs or journal lookups fail |
| [DEBUGGING_GUIDE.md](DEBUGGING_GUIDE.md) | Logs, the database, the API, and the test suite |
| [DEBUGGING_JAVASCRIPT.md](DEBUGGING_JAVASCRIPT.md) | The browser console and the helpers in `static/js/debug.ts` |

Install and first-launch problems (Mac "damaged" or "unidentified developer",
Windows SmartScreen) are in [INSTALL.md](../../INSTALL.md).

## Where things are

- **Logs:** `logs/app.log` inside your data folder, and the terminal if you
  started the app from one.
- **Database:** `genetic_profile.db` inside your data folder.
- **Which folder is your data folder:** the `HEALTH_LEDGER_DATA_DIR` line in the
  settings file listed at the end of [INSTALL.md](../../INSTALL.md), or the
  path shown on the first screen.

When you report a problem, do not paste records or the contents of a log that
may contain them. Describe what you did and what the page said.
