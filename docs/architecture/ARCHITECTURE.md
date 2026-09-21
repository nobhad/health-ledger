# System Architecture

**Last Updated**: December 7, 2025

## Overview

The Genetic Profile Database is a Flask-based web application that manages and queries genetic profile data. It uses SQLite for data storage, provides a RESTful API, and includes a web interface for interactive querying.

**Architecture Type**: Monolithic web application with database backend

---

## Table of Contents

- [System Components](#system-components)
- [Technology Stack](#technology-stack)
- [Data Flow](#data-flow)
- [Database Architecture](#database-architecture)
- [Application Structure](#application-structure)
- [Security Considerations](#security-considerations)
- [Deployment Architecture](#deployment-architecture)

---

## System Components

### 1. Web Application (Flask)

**Purpose**: HTTP server and request handling

**Components:**

- Route handlers for web pages
- API endpoints for data access
- Template rendering
- Static file serving

**File**: `app.py`

### 2. Database Layer

**Purpose**: Data persistence and querying

**Components:**

- SQLite database
- Database manager class
- Schema definitions
- Query methods

**Files**:

- `database_manager.py`
- `genetic_profile_db_schema.sql`

### 3. Frontend

**Purpose**: User interface

**Components:**

- HTML templates
- CSS styling
- JavaScript for interactivity
- Multiselect components

**Files**:

- `templates/`
- `static/css/`
- `static/js/`

### 4. Data Processing Scripts

**Purpose**: Data import and transformation

**Components:**

- Markdown import
- Citation management
- HTML generation
- Summary generation

**Files**: `scripts/`

---

## Technology Stack

### Backend

- **Python 3.6+**: Programming language
- **Flask**: Web framework
- **SQLite3**: Database
- **Markdown**: Document processing

### Frontend

- **HTML5**: Markup
- **CSS3**: Styling
- **JavaScript (ES6+)**: Interactivity
- **Jinja2**: Template engine

### Development Tools

- **logging**: Application logging
- **pathlib**: File path handling
- **re**: Regular expressions
- **json**: JSON processing

---

## Data Flow

### Request Flow

```text
Browser Request
    ↓
Flask App (app.py)
    ↓
Route Handler
    ↓
Database Manager (database_manager.py)
    ↓
SQLite Database
    ↓
Response (JSON/HTML)
    ↓
Browser
```

### Data Import Flow

```text
Markdown Document
    ↓
Import Script (scripts/import_from_markdown.py)
    ↓
Parse & Extract Data
    ↓
Database Manager
    ↓
SQLite Database
```

### HTML Generation Flow

```text
Markdown Document
    ↓
Generate HTML Script (scripts/generate_html.py)
    ↓
Convert Citations
    ↓
Markdown → HTML
    ↓
HTML File (output/)
```

---

## Database Architecture

### Database Type

**SQLite** - File-based relational database

**Advantages:**

- No server required
- Easy backup (copy file)
- ACID compliant
- Good for single-user/small-scale applications

**Configuration:**

- WAL mode enabled for better concurrency
- Thread-safe connections
- Foreign key constraints enabled

### Schema Design

**Core Tables:**

- `genes` - Gene information
- `snps` - Single nucleotide polymorphisms
- `genotypes` - User genotypes
- `citations` - Reference citations
- `research_references` - Enhanced research references

**Association Tables:**

- `trait_associations` - Gene-trait relationships
- `health_condition_associations` - Gene-condition relationships
- `gene_gene_interactions` - Gene interaction network

**Linking Tables:**

- `gene_trait_citations` - Citations for traits
- `gene_health_citations` - Citations for conditions
- `research_finding_citations` - Citations for findings

**Pharmacogenomic Tables:**

- `pharmacogenomic_data` - Drug metabolism data
- `gene_pharmacogenomic_drugs` - Medication associations

**Primary Source Tables:**

- `primary_sources` - Source documents
- `primary_source_findings` - Findings from sources

**Views:**

- `gene_summary` - Gene overview
- `gene_trait_view` - Trait associations
- `gene_health_view` - Health condition associations
- `gene_interaction_view` - Gene interactions
- `gene_pharmacogenomic_view` - Pharmacogenomic data

### Relationships

```text
genes (1) ──→ (many) snps
genes (1) ──→ (many) genotypes
genes (1) ──→ (many) trait_associations
genes (1) ──→ (many) health_condition_associations
genes (1) ──→ (many) pharmacogenomic_data
genes (1) ──→ (many) gene_gene_interactions

citations (many) ←──→ (many) trait_associations
citations (many) ←──→ (many) health_condition_associations
citations (many) ←──→ (many) research_findings
```

---

## Application Structure

### Directory Layout

```text
genetic_profile/
├── app.py                    # Flask application
├── database_manager.py       # Database interface
├── config.py                 # Configuration & logging
├── genetic_profile.db        # SQLite database
│
├── templates/                # HTML templates
│   ├── base.html
│   ├── query.html
│   ├── profile.html
│   ├── summary.html
│   └── components.html
│
├── static/                   # Static assets
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── multiselect.js
│       └── query.js
│
├── scripts/                  # Utility scripts
│   ├── generate_html.py
│   ├── import_from_markdown.py
│   ├── citation_overhaul.py
│   └── ...
│
├── docs/                     # Documentation
│   ├── features/
│   ├── api/
│   └── architecture/
│
├── output/                   # Optional export files (not used by web app)
│   └── (generated on-demand, not stored)
│
└── primary_sources/          # Source documents
    └── ...
```

### Module Organization

**app.py**:

- Flask application setup
- Route definitions
- Request handling
- Error handling

**database_manager.py**:

- Database connection management
- CRUD operations
- Query methods
- Relationship management

**config.py**:

- Application configuration
- Logging setup
- Path definitions

---

## Security Considerations

### Current Security Measures

1. **Input Validation**
   - Parameter validation in API endpoints
   - SQL parameterization (prevents injection)
   - Type checking

2. **Error Handling**
   - Detailed errors only in DEBUG mode
   - Generic errors in production
   - Error logging

3. **Database Security**
   - Parameterized queries
   - Foreign key constraints
   - Input sanitization

### Security Recommendations

For production deployment:

1. **Authentication**
   - Add user authentication
   - API key system
   - Session management

2. **HTTPS**
   - Use SSL/TLS certificates
   - Encrypt data in transit

3. **Data Protection**
   - Encrypt sensitive data
   - Regular backups
   - Access controls

4. **Rate Limiting**
   - Limit API requests
   - Prevent abuse
   - DDoS protection

---

## Deployment Architecture

### Development

```text
Local Machine
    ↓
Flask Development Server (localhost:5001)
    ↓
SQLite Database (local file)
    ↓
Browser (localhost:5001)
```

### Production (Recommended)

```text
Web Server (Nginx/Apache)
    ↓
WSGI Server (Gunicorn/uWSGI)
    ↓
Flask Application
    ↓
SQLite Database
    ↓
Static Files (CDN optional)
```

### Alternative: Container Deployment

```text
Docker Container
    ├── Flask Application
    ├── SQLite Database
    └── Static Files
    ↓
Container Orchestration (Docker Compose/Kubernetes)
```

---

## Thread Safety

### Database Connections

**Thread-Local Storage:**

- Each Flask request thread gets its own database connection
- Connections stored in thread-local storage
- Automatically closed after request

**Implementation:**

```python
_local = threading.local()

def get_db():
    if not hasattr(_local, 'db'):
        _local.db = GeneticProfileDB()
    return _local.db
```

### SQLite Configuration

- `check_same_thread=False`: Allows connections from different threads
- WAL mode: Better concurrency for read/write operations
- Thread-local connections: Prevents connection sharing issues

---

## Performance Considerations

### Database Optimization

1. **Indexes**
   - Indexed on frequently queried columns
   - Unique indexes on gene_symbol, citation_number

2. **Views**
   - Pre-computed views for common queries
   - Reduces JOIN complexity

3. **Query Optimization**
   - Use views for complex queries
   - Limit result sets
   - Efficient JOINs

### Caching

**Current**: No caching implemented

**Recommendations**:

- Cache frequently accessed data
- Cache API responses
- Use Redis for distributed caching

### Scalability

**Current Limitations**:

- SQLite: Single-writer limitation
- File-based: Not suitable for high concurrency

**Scaling Options**:

- Migrate to PostgreSQL for multi-user
- Add read replicas
- Implement connection pooling
- Use CDN for static files

---

## Monitoring and Logging

### Logging System

**Location**: `logs/app.log`

**Log Levels**:

- DEBUG: Detailed diagnostic information
- INFO: General informational messages
- WARNING: Warning messages
- ERROR: Error messages
- CRITICAL: Critical errors

### Monitoring

**Current**: File-based logging

**Recommendations**:

- Application performance monitoring (APM)
- Error tracking (Sentry)
- Health check endpoints
- Metrics collection

---

## Related Files

### Documentation

- `docs/DEBUGGING_GUIDE.md` - Debugging instructions
- `docs/DATABASE_README.md` - Database documentation
- `docs/features/` - Feature documentation

### Configuration

- `config.py` - Application configuration
- `.gitignore` - Version control exclusions

---

## Future Architecture Improvements

- [ ] Migrate to PostgreSQL for production
- [ ] Add Redis caching layer
- [ ] Implement API versioning
- [ ] Add GraphQL API
- [ ] Microservices architecture
- [ ] Event-driven architecture
- [ ] Real-time updates (WebSockets)
- [ ] Search engine integration (Elasticsearch)
