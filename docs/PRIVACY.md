# Privacy & Security Documentation

## Privacy-First Architecture

This application is designed with privacy as the primary concern. Your health records remain on your local machine and are never transmitted to external servers. The one outbound request the application can make is a journal search you start yourself on the References page; see [No External Services](#no-external-services).

## Localhost-Only Access

The application is configured to run on `127.0.0.1` (localhost) only. This means:

- The server is only accessible from your local machine
- No other machine can connect to it
- Your health data cannot be accessed by others on your network

### Configuration

The application is configured in `config.py`:

```python
HOST = '127.0.0.1'  # Localhost-only for privacy
ALLOW_EXTERNAL_ACCESS = False
```

`app.py` binds to `HOST` and adds `X-Content-Type-Options`, `X-Frame-Options` and `X-XSS-Protection` headers to every response. It sends no CORS headers, so a web page open in your browser cannot read the app's API.

## Single-User Design

This application is designed for single-user, personal use:

- SQLite database stores all data locally in a single file
- No user authentication system (not needed for single-user)
- All data belongs to one person (you)

## Cloud Backup & Export

The application never uploads anything to a cloud service. If you want a copy
in cloud storage you can export one and put it there yourself. That is your
choice to send the file to that provider, and the database is not encrypted
(see [SECURITY.md](../SECURITY.md)):

### Creating Backups

1. Use the **Backup** page in the web application (`/backup`)
2. Or use the command-line script:

   ```bash
   python3 scripts/backup_database.py --backup
   ```

### Exporting Data

Export your database to a file for cloud storage sync:

1. **SQLite Database Export:**

   ```bash
   python3 scripts/backup_database.py --export /path/to/my_backup.db
   ```

2. **JSON Export:**

   ```bash
   python3 scripts/backup_database.py --json /path/to/my_backup.json
   ```

### Cloud Storage Sync

To sync backups to cloud storage:

1. Create backups using the methods above
2. Locate the `backups/` folder inside your data folder (the folder you chose
   on the first screen)
3. Add the `backups/` directory to your cloud storage sync folder:
   - **Dropbox**: Add `backups/` to your Dropbox folder
   - **iCloud**: Add `backups/` to your iCloud Drive
   - **Google Drive**: Add `backups/` to your Google Drive folder
4. Backups will automatically sync to the cloud

**Important**: Only the `backups/` directory should be synced. Do not sync the main database file while the application is running, as this can cause corruption.

## Security Best Practices

1. **Keep the application local**: Never configure the application to accept external connections
2. **Regular backups**: Create backups regularly, especially before making significant changes
3. **Secure your machine**: Use strong passwords and encryption on your computer
4. **Review cloud sync settings**: Ensure only backup files are synced, not the live database
5. **Monitor access**: Check that the application is only accessible on localhost

## Data Portability

All data is stored in a single SQLite database file (`genetic_profile.db`). This file:

- Can be easily copied and moved
- Can be exported to JSON for portability
- Can be backed up to cloud storage
- Contains all your health data in one place

## No External Services

This application does not:

- Send your records to external servers
- Use cloud-based services
- Require an internet connection
- Store data in third-party databases

All processing happens locally on your machine.

There is one exception, and it is a request you make. On the References page,
when you type a search and press **Look up**, the application sends the words
you typed to Europe PMC (a public index of journal articles run by EMBL-EBI).
Fetching the abstract of an article you already saved sends that article's
PubMed id instead. Nothing from your records is sent: no names, results,
genotypes or files. It never happens automatically. A search term can itself
be revealing, such as the name of a gene or condition. See
[References](features/REFERENCES.md).

## What stays on your computer

Your health data:

- Stays on your local machine
- Is never transmitted externally (a journal search you press sends only the
  words you typed, not your records)
- Is reachable only from this computer. There is no password and no
  encryption, so anyone who can use your logged-in computer can open it
- Can be exported and backed up at your discretion
