# Documentation Overhaul Plan
**Date:** December 7, 2025

## Current Issues

1. **Duplicate Content:**
   - DATABASE_README.md vs DATABASE_COMPLETE.md (both cover database)
   - DEBUGGING_GUIDE.md vs DEBUGGING_JAVASCRIPT.md (overlap)
   - WEB_QUERY_README.md vs QUICK_START.md (overlap)
   - TROUBLESHOOTING.md (overlaps with debugging)

2. **Outdated/Historical Files:**
   - CITATION_OVERHAUL_SUMMARY.md (historical)
   - DISPLAY_INCONSISTENCIES.md (may be outdated)
   - center_for_human_genetics_* (extracted data files)

3. **Misplaced Files:**
   - Your_Genetic_Profile_Summary.md (generated content, not documentation)
   - TEMPLATE_GENE_SECTION.md (template, not user docs)

4. **Structure Issues:**
   - Files scattered in root of docs/
   - No clear organization
   - Cross-references may be broken

## Proposed Structure

```
docs/
├── README.md                    # Main index (UPDATED)
├── QUICK_START.md              # Consolidated quick start
│
├── database/                    # Database documentation
│   ├── README.md               # Main database doc (from DATABASE_COMPLETE.md)
│   ├── SCHEMA.md               # Schema reference
│   └── QUERIES.md              # Query examples
│
├── api/                        # API documentation
│   └── API_REFERENCE.md        # Keep as-is
│
├── architecture/               # Architecture docs
│   └── ARCHITECTURE.md         # Keep as-is
│
├── features/                   # Feature documentation
│   ├── QUERY_INTERFACE.md
│   ├── PROFILE_VIEWER.md
│   ├── SUMMARY_GENERATOR.md
│   ├── DATA_IMPORT.md
│   ├── CITATION_MANAGEMENT.md
│   ├── PHARMACOGENOMIC.md
│   └── DATABASE_QUERIES.md
│
├── guides/                     # User guides
│   ├── HEALTHCARE_SUMMARY.md   # From HEALTHCARE_SUMMARY_GUIDE.md
│   ├── PRIMARY_SOURCES.md      # From PRIMARY_SOURCES_EXTRACTION.md
│   └── WEB_INTERFACE.md        # Consolidated from WEB_QUERY_README.md + QUICK_START.md
│
├── troubleshooting/            # Troubleshooting docs
│   ├── DEBUGGING.md            # Consolidated debugging guide
│   └── COMMON_ISSUES.md        # From TROUBLESHOOTING.md
│
├── templates/                  # Template files
│   └── GENE_SECTION.md         # From TEMPLATE_GENE_SECTION.md
│
└── archive/                    # Historical/summary files
    ├── CITATION_OVERHAUL_SUMMARY.md
    ├── DISPLAY_INCONSISTENCIES.md
    ├── center_for_human_genetics_extracted_text.txt
    └── center_for_human_genetics_summary.md
```

## Actions

1. Create new folder structure
2. Move/consolidate files
3. Update all cross-references
4. Update README.md
5. Remove outdated content
6. Verify all links work

