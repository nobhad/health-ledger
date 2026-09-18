# Privacy & Security Documentation

## Privacy-First Architecture

This application is designed with privacy as the primary concern. All health data remains on your local machine and is never transmitted to external servers.

## Localhost-Only Access

The application is configured to run on `127.0.0.1` (localhost) only. This means:

- The server is only accessible from your local machine
- No external network access is allowed
- Your health data cannot be accessed by others on your network

### Configuration

The application is configured in `config.py`:

```python
HOST = '127.0.0.1'  # Localhost-only for privacy
ALLOW_EXTERNAL_ACCESS = False
```

The Flask application in `app.py` includes security headers to prevent accidental external exposure.

## Single-User Design

This application is designed for single-user, personal use:

- SQLite database stores all data locally in a single file
- No user authentication system (not needed for single-user)
- All data belongs to one person (you)

## Cloud Backup & Export

While the application runs locally, you can export your data for cloud backup:

### Creating Backups

1. Use the Backup interface in the web application (`/backup`)
2. Or use the command-line script:
   ```bash
   python3 scripts/backup_database.py --backup
   ```

### Exporting Data

Export your database to a file for cloud storage sync:

1. **SQLite Database Export:**
   ```bash
   python3 scripts/backup_database.py --export backups/my_backup.db
   ```

2. **JSON Export:**
   ```bash
   python3 scripts/backup_database.py --json backups/my_backup.json
   ```

### Cloud Storage Sync

To sync backups to cloud storage:

1. Create backups using the methods above
2. Locate the `backups/` directory
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

- Send data to external servers
- Use cloud-based services
- Require internet connection (except for downloading research papers, which is optional)
- Store data in third-party databases

All processing happens locally on your machine.

## Privacy Guarantee

Your health data:

- Stays on your local machine
- Is never transmitted externally
- Is only accessible by you
- Can be exported and backed up at your discretion

The application is designed to give you complete control over your health data.

