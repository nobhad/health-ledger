# Database-Driven Architecture

**Last Updated:** December 7, 2025

## Overview

**All content is generated dynamically from the database** - there are NO static HTML files.

## Key Principles

1. ✅ **Everything pulls from database** - No pre-generated files
2. ✅ **Always up-to-date** - Content reflects current database state
3. ✅ **No static pages** - All pages generated on-demand
4. ✅ **Single source of truth** - Database is the only source

---

## Routes

### `/profile`
- **Source:** Database (via `profile_generator.py`)
- **Generates:** Complete genetic profile HTML
- **Updates:** Automatically reflects database changes

### `/summary`
- **Source:** Database (via `generate_personalized_summary.py`)
- **Generates:** Personalized summary HTML
- **Updates:** Automatically reflects database changes

### `/api/*`
- **Source:** Database (direct queries)
- **Returns:** JSON data
- **Updates:** Real-time database queries

---

## No Static Files

❌ **DO NOT USE:**
- `output/genetic_profile.html` - Not used by web app
- `output/Your_Genetic_Profile_Summary.html` - Not used by web app
- `scripts/generate_html.py` - Legacy script, not used by web app

✅ **USE INSTEAD:**
- `profile_generator.py` - Generates profile from database
- `scripts/generate_personalized_summary.py` - Generates summary from database
- Database queries via `database_manager.py`

---

## Updating Content

To update displayed content:

1. **Update database** (add/modify genes, traits, conditions)
2. **Refresh page** - Content automatically reflects changes
3. **No regeneration needed** - Everything is dynamic

---

## Benefits

- ✅ Always current - No stale content
- ✅ Single source of truth - Database only
- ✅ Easy updates - Change database, content updates
- ✅ No file management - No static files to maintain
- ✅ Consistent data - All pages use same database

---

**Status:** ✅ Fully Database-Driven

