# Security and privacy

Health Ledger holds medical records. This is what it does with them, and how
to tell me if something here is wrong.

## Reporting a vulnerability

Please report privately first, not as a public issue.

- GitHub: use **Security → Report a vulnerability** on this repository
  (private advisories).
- Or: <https://nobhad.codes>

Tell me what you found, how to reproduce it, and what an attacker gets. I will
acknowledge within a week. There is no bounty — this is a personal project —
but I will credit you in the changelog if you want.

**Never include real medical records, names or dates of birth in a report.**
Use made-up data to demonstrate the problem.

## The privacy model

- **Nothing leaves your machine.** No account, no sync, no telemetry, no crash
  reporting, no update check. The app makes no outbound network request while
  you use it.
- **The server binds to `127.0.0.1`.** Not `0.0.0.0`. Another machine on your
  network cannot reach it, and neither can anything on the internet.
- **No CORS headers.** A website open in the same browser cannot read the API,
  even while the server is running.
- **Your records live in a folder you choose**, outside the app. Uninstalling
  the app does not touch them.
- **No encryption at rest.** The database is a plain SQLite file. Anyone with
  access to your user account, or to an unencrypted backup drive, can read it.
  Turn on FileVault (macOS) or BitLocker (Windows). Encrypted backups are on
  the roadmap, not done.
- **No password on the app itself.** Anyone who can use your logged-in
  computer can open it. It is guarded by your OS account, nothing more.

## Known limitations

These are deliberate, and you should know about them before trusting the app
with anything.

| | |
| --- | --- |
| Local processes | Any program running as your user can reach `127.0.0.1:5001` and read the API. This is inherent to a local web app with no auth. |
| Unsigned downloads | The Mac and Windows builds are not signed, so your OS cannot verify who built them. See [INSTALL.md](INSTALL.md). If this matters to you, run from source. |
| Reference data | The pharmacogenomic and variant tables are compiled from public sources (dbSNP, CPIC, Ensembl) and checked by `scripts/check_variant_reference.py`. Correct naming is not clinical validation. Nothing here is a reason to change a medication. |
| Not a medical device | Not reviewed by any regulator. See [LICENSE](LICENSE) §6. |

## For contributors

The repository must never contain private data. `scripts/check_private_data.py`
scans every tracked file for record file names, home paths, dates of birth,
medical record numbers and clinical narrative. The test suite runs it and a
pre-commit hook blocks a commit that fails it.

If you send a patch, run it first:

```bash
python3 scripts/check_private_data.py
```

## Supported versions

The latest release is the supported one. Fixes go into a new release rather
than being backported.
