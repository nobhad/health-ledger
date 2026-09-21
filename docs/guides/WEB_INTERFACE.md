# Web Query Interface Guide

**Last Updated:** December 7, 2025

## Overview

This web application provides an interactive interface to query your genetic profile database from your web browser.

> **Quick Start:** See [QUICK_START.md](QUICK_START.md) for a faster getting started guide.

## Features

- **Query by Health Condition**: Find all genes associated with a specific health condition (e.g., ADHD, anxiety, depression)
- **Query by Trait**: Find all genes associated with a specific trait (e.g., pain sensitivity, stress response)
- **Gene Information**: Get comprehensive information about a specific gene including traits, conditions, interactions, and pharmacogenomic data
- **View All Genes**: See all genes in the database
- **Pharmacogenomic Data**: View medication metabolism information for all genes

## How to Use

### Starting the Web Server

1. Open Terminal
2. Navigate to the genetic_profile directory:

   ```bash
   cd path/to/health-ledger
   ```

3. Start the web server:

   ```bash
   python3 web_query_app.py
   ```

   The server will automatically use port 5001 (port 5000 is often used by AirPlay on macOS).

   To use a different port:

   ```bash
   python3 web_query_app.py 8080
   ```

   Or use the convenience script:

   ```bash
   ./start_web_query.sh
   ```

4. Open your web browser and go to:

   ```text
   http://localhost:5001
   ```

   Or try:

   ```text
   http://127.0.0.1:5001
   ```

### Using the Query Interface

1. **Query by Condition**:
   - Enter a health condition (e.g., "ADHD", "anxiety", "depression")
   - Click "Search"
   - Results show all genes associated with that condition

2. **Query by Trait**:
   - Enter a trait (e.g., "pain sensitivity", "stress response")
   - Click "Search"
   - Results show all genes associated with that trait

3. **Get Gene Info**:
   - Select a gene from the dropdown
   - Click "Get Gene Info"
   - See comprehensive information including traits, conditions, interactions, and pharmacogenomic data

4. **View All Genes**:
   - Click "Show All Genes"
   - See a list of all genes in the database

5. **View Pharmacogenomic Data**:
   - Click "Show Medication Metabolism"
   - See medication metabolism information for all genes

### Navigation

- **Query Interface**: Main page for querying the database
- **View Full Profile**: Opens your complete genetic profile document
- **View Summary**: Opens your personalized summary document

## Stopping the Server

Press `Ctrl+C` in the terminal where the server is running.

## Technical Details

- **Framework**: Flask (Python web framework)
- **Database**: SQLite (genetic_profile.db)
- **Port**: 5001 (default, 5000 is often used by AirPlay on macOS)
- **API Endpoints**:
  - `/api/genes-by-condition?condition=ADHD`
  - `/api/genes-by-trait?trait=anxiety`
  - `/api/gene-info?gene=ADRA2A`
  - `/api/all-genes`
  - `/api/pharmacogenomic`

## Troubleshooting

- **Port already in use**: The app defaults to port 5001. If that's also busy, run with a different port: `python3 web_query_app.py 8080`
- **Database not found**: Make sure `genetic_profile.db` exists in the same directory
- **Module not found**: Install Flask with `pip3 install flask`
