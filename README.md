# Health Ledger

A comprehensive system for documenting, managing, and querying genetic profile data from pharmacogenomic testing, with support for both non-pharmacogenomic traits and drug metabolism information.

## 🎯 Project Status

**✅ PRODUCTION-READY** - All high and medium priority items complete!

### Completed Features

- ✅ **Complete Database System** - SQLite database with full schema
- ✅ **Web Query Interface** - Interactive web application for querying genetic data
- ✅ **Data Import** - Automated import from markdown documents
- ✅ **Input Validation** - Comprehensive validation on all API endpoints
- ✅ **Error Handling** - Standardized error responses and logging
- ✅ **Test Suite** - Unit and integration tests (14/14 passing)
- ✅ **Documentation** - Complete documentation for all features
- ✅ **Pharmacogenomic Data** - Full support for drug metabolism information
- ✅ **Gene-Gene Interactions** - Import and query gene interaction data

## 📁 Project Structure

```
health-ledger/
├── app.py                      # Flask web application
├── database_manager.py          # Database API
├── validation.py               # Input validation utilities
├── config.py                   # Application configuration
├── requirements.txt            # Python dependencies
├── .gitignore                 # Git ignore rules
├── genetic_profile.db         # SQLite database
├── genetic_profile_db_schema.sql  # Database schema
│
├── templates/                  # Jinja templates (base, header, footer, components + one per page)
│
├── static/                     # Static assets
│   ├── css/
│   │   ├── health-ledger.css  # Bundle entry (imports, in cascade-layer order)
│   │   ├── design-system/     # VENDORED no-bhad-codes tokens/reset/fonts (see VENDORED.md)
│   │   ├── app-tokens.css     # The few tokens this app adds
│   │   ├── base.css           # Element defaults
│   │   ├── components.css     # ALL reusable component classes
│   │   ├── layout.css         # Header, nav, footer, grids
│   │   ├── pages.css          # Rendered documents, page-specific rules
│   │   ├── utilities.css      # Atomic helpers
│   │   ├── dist/              # Built bundle (npm run build:css) — what base.html loads
│   │   ├── pdf.css            # WeasyPrint-only stylesheet for generated PDFs
│   │   └── print.css          # Print rules for generated PDFs
│   ├── fonts/                 # Inconsolata (self-hosted)
│   └── js/
│       ├── debug.js           # Debug utilities
│       ├── multiselect.js     # Multiselect dropdowns
│       └── query.js           # Query interface logic
│
├── scripts/                    # Utility scripts
│   ├── import_from_markdown.py # Import markdown to database
│   ├── generate_html.py       # Generate HTML from markdown
│   └── ...                    # Other utility scripts
│
├── docs/                       # Documentation
│   ├── README.md              # Documentation index
│   ├── api/                   # API documentation
│   ├── architecture/          # Architecture docs
│   ├── features/              # Feature documentation
│   └── ...                    # Other documentation
│
├── tests/                      # Test suite
│   ├── test_validation.py     # Validation tests
│   ├── test_database_manager.py # Database tests
│   └── test_api_endpoints.py  # API integration tests
│
├── primary_sources/            # Primary source documents
└── output/                     # Generated output files
```

## Where your data lives

Everything private — the SQLite database, `primary_sources/`, `output/`, `logs/`
and `backups/` — sits under **one directory outside this repository**, named by
`HEALTH_LEDGER_DATA_DIR`. Set it once in a git-ignored `.env` (copy
`.env.example`):

```
HEALTH_LEDGER_DATA_DIR=~/HealthLedgerData
```

`config.py` derives every data path from it. Left unset, the paths fall back to
the project folder, where they are git-ignored. Nothing under the data
directory is ever committed; `python3 scripts/check_private_data.py` (also run
by the tests and the pre-commit hook) refuses record file names, home paths and
patient narrative in tracked files.

## 🚀 Quick Start

1. Run `./start.sh` (Mac/Linux; or double-click `Health Ledger.command`) or
   `start.bat` (Windows). The first run creates a Python environment and
   installs what it needs; every run starts the server and opens
   http://127.0.0.1:5001 in your browser.
2. The first screen asks where your records should live (a "Health Ledger"
   folder in your home folder is proposed; type another if you prefer) and
   how to begin:
   - **Start fresh** — begin with an empty ledger and add records later.
   - **Import a database** — choose the `.db` file Health Ledger made
     before (a backup, an export, a copy from another computer). It is
     checked before it replaces anything, and if the ledger already holds
     records they are backed up first.

   The folder choice is saved to the git-ignored `.env` for the next launch.

   That screen stays at `/setup` (also linked from the Backup page) for
   restoring a backup or importing later on.

### Running by hand

```bash
pip3 install -r requirements.txt
python3 app.py            # http://localhost:5001
```

### Importing Data

```bash
# Import from markdown document
python3 scripts/import_from_markdown.py
```

### Running Tests

```bash
# Run all tests
python3 -m unittest discover tests

# Run specific test file
python3 -m unittest tests.test_validation
```

## 📚 Documentation

Complete documentation is available in the `docs/` directory:

- **[Main Documentation](docs/README.md)** - Complete documentation index
- **[API Reference](docs/api/API_REFERENCE.md)** - All API endpoints
- **[Architecture](docs/architecture/ARCHITECTURE.md)** - System architecture
- **[Features](docs/features/)** - Feature-specific documentation
- **[Debugging Guide](docs/troubleshooting/DEBUGGING_GUIDE.md)** - Troubleshooting

## 🔧 Key Features

### Database System

- **Every gene** documented with traits, conditions, and interactions
- **Pharmacogenomic data** for drug metabolism
- **Gene-gene interactions** for understanding genetic relationships
- **Primary source integration** from medical records and test results
- **Citation management** with PubMed and database references

### Web Interface

- **Query Interface** - Search by gene, condition, or trait
- **Multiselect Dropdowns** - Searchable, filterable options
- **Full Profile Viewer** - Complete genetic profile document
- **Personalized Summary** - Key findings and recommendations
- **Responsive Design** - Works on all devices

### Data Management

- **Automated Import** - Import from markdown documents
- **Data Validation** - Input validation on all endpoints
- **Error Handling** - Comprehensive error handling and logging
- **Thread Safety** - Thread-safe database connections

## 🧪 Testing

The application includes a comprehensive test suite:

- **Unit Tests** - Validation and database operations
- **Integration Tests** - API endpoint testing
- **Test Coverage** - All critical paths covered

Run tests with:
```bash
python3 -m unittest discover tests -v
```

## 🔒 Security

- **Input Validation** - All inputs validated and sanitized
- **XSS Protection** - HTML tag filtering
- **SQL Injection Prevention** - Parameterized queries
- **Request Size Limits** - Protection against DoS attacks

## 📊 Database Schema

The database includes tables for:
- Genes, SNPs, Genotypes
- Trait and health condition associations
- Gene-gene interactions
- Pharmacogenomic data
- Citations and references
- Primary source documents
- Health metrics and findings

See [Database Schema](genetic_profile_db_schema.sql) for complete details.

## 🛠️ Development

### Adding New Features

1. Create feature branch
2. Implement feature with tests
3. Update documentation
4. Run test suite
5. Submit for review

### Code Standards

- Follow PEP 8 style guide
- Add docstrings to all functions
- Include type hints where appropriate
- Write tests for new features
- Update documentation

## 📝 License

Personal medical project - private use only.

## 📞 Support

For issues or questions:
1. Check [Debugging Guide](docs/troubleshooting/DEBUGGING_GUIDE.md)
2. Review [Troubleshooting](docs/troubleshooting/README.md)
3. Check [API Reference](docs/api/API_REFERENCE.md)

---

**Last Updated:** December 7, 2025  
**Status:** Production-Ready ✅  
**Version:** 1.0.0

## Running

```bash
./start.sh            # macOS / Linux — or double-click "Health Ledger.command" on a Mac
start.bat             # Windows — double-click
npm run dev           # same as ./start.sh
```

The first run creates `./venv` and installs `requirements.txt`; every run starts the
server on http://127.0.0.1:5001 and opens it in your browser. The server only listens on
this machine. On Windows, PDF generation (WeasyPrint) also needs GTK; see
<https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows>.


## Styling

The UI uses the **no-bhad-codes design system** (its token layer, reset and fonts), vendored
into `static/css/design-system/` by `scripts/sync_design_system.sh`. The app's own
stylesheets reference only those tokens plus the handful in `static/css/app-tokens.css` —
no literal colours or sizes in component CSS. Cascade layers follow the design system's
`layer-order.css`; `portal-theme.css` is imported last and unlayered, keyed to
`<body data-page="ledger">`, and provides the light/dark palette (toggle in the header,
stored under `health-ledger-theme` in localStorage).

```bash
npm install
npm run build:css        # static/css/health-ledger.css -> static/css/dist/health-ledger.css
npm run watch:css        # rebuild on change
npm run sync:design-system   # re-copy tokens from ../no-bhad-codes and rebuild
```

The built bundle is committed so the Flask app runs without Node. Generated PDFs
(WeasyPrint) do not use the bundle; they load `pdf.css` + `print.css`.
