# Documentation

Documentation for Health Ledger, a personal medical record app that runs on
your own computer. For what it is and how to install it, start with the
[main README](../README.md) and [INSTALL.md](../INSTALL.md).

## Index

### Getting started

- [Quick Start Guide](guides/QUICK_START.md)
- [Web Query Interface Guide](guides/WEB_INTERFACE.md)
- [Healthcare Summary Guide](guides/HEALTHCARE_SUMMARY.md)
- [Primary Sources Extraction Guide](guides/PRIMARY_SOURCES.md)

### How it works

- [Architecture](architecture/ARCHITECTURE.md)
- [API Reference](api/API_REFERENCE.md)
- [Database overview](database/OVERVIEW.md) and
  [Database reference](database/README.md) (also reachable from
  [DATABASE_README.md](DATABASE_README.md))
- [Privacy and security](PRIVACY.md)

### Pages and features

- [Query page](features/QUERY_INTERFACE.md)
- [Summary](features/SUMMARY_GENERATOR.md)
- [Full profile](features/PROFILE_VIEWER.md)
- [Data import](features/DATA_IMPORT.md)
- [References](features/REFERENCES.md)
- [Citation management](features/CITATION_MANAGEMENT.md)
- [Pharmacogenomic data](features/PHARMACOGENOMIC.md)
- [Database queries](features/DATABASE_QUERIES.md)

### Working on the code

- [Development](DEVELOPMENT.md): running from source, building, the rules
- [Tests](../tests/README.md)
- [Packaging and releases](../packaging/README.md)
- [Contributing](../CONTRIBUTING.md)
- [Gene section template](templates/TEMPLATE_GENE_SECTION.md)

### Troubleshooting

- [Troubleshooting guide](troubleshooting/README.md)
- [Common issues](troubleshooting/COMMON_ISSUES.md)
- [Debugging guide](troubleshooting/DEBUGGING_GUIDE.md)
- [JavaScript debugging](troubleshooting/DEBUGGING_JAVASCRIPT.md)

### Project files

- [Changelog](../CHANGELOG.md): what changed, by version

## What is in this folder

| Path | Holds |
| --- | --- |
| `README.md` | This index. |
| `DEVELOPMENT.md`, `PRIVACY.md`, `DATABASE_README.md` | Top-level pages: development rules, privacy and security, a pointer to the database docs. |
| `guides/` | Walkthroughs for using the app. |
| `database/` | Database overview and reference. |
| `api/` | The API reference. |
| `architecture/` | How the modules fit together. |
| `features/` | One page per page or feature of the app. |
| `troubleshooting/` | Common problems and debugging. |
| `templates/` | A template for a gene section. |
| `archive/` | Notes from past work, kept as written. They describe the earlier program this one was renamed from, and are not kept up to date. |
