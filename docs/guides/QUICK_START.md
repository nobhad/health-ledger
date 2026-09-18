# Quick Start Guide

**Last Updated:** December 7, 2025

> **For detailed information, see [WEB_INTERFACE.md](WEB_INTERFACE.md)**

## Start the Server

```bash
cd path/to/health-ledger
python3 web_query_app.py
```

The server will start on **port 5001** (port 5000 is often used by AirPlay on macOS).

## Open in Browser

Once the server is running, open your browser to:

**http://localhost:5001**

or

**http://127.0.0.1:5001**

## What You Can Do

- **Query by Health Condition**: Enter "ADHD", "anxiety", "depression", etc.
- **Query by Trait**: Enter "pain sensitivity", "stress response", etc.
- **Get Gene Info**: Select a gene from the dropdown to see all its associations
- **View All Genes**: See every gene in your database
- **View Pharmacogenomic Data**: See medication metabolism information

## If Port 5001 is Also Busy

Run with a different port:
```bash
python3 web_query_app.py 8080
```

Then access: http://localhost:8080

## Stop the Server

Press `Ctrl+C` in the terminal where the server is running.

