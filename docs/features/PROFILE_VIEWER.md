# Profile Viewer Feature

**Last Updated**: December 7, 2025

## Overview

The Profile Viewer displays the complete genetic profile document with all gene information, trait associations, health conditions, citations, and pharmacogenomic data. It provides a comprehensive view of the entire genetic profile in a readable, navigable format.

**Key Features:**

- 📄 Complete genetic profile document display
- 🔗 Clickable citation links
- 📑 Table of contents navigation
- 🎨 Clean, readable formatting
- 📱 Responsive design

---

## Table of Contents

- [Route](#route)
- [HTML Generation](#html-generation)
- [Citation Links](#citation-links)
- [Template Structure](#template-structure)
- [Styling](#styling)
- [Error Handling](#error-handling)
- [Related Files](#related-files)

---

## Route

### GET /profile

**Purpose**: Display the full genetic profile HTML document.

**Handler**: `app.profile()`

**Process**:
1. **Queries database** for all genes, traits, conditions, and citations
2. **Generates HTML dynamically** from database using `profile_generator.py`
3. Renders with `templates/profile.html`
4. Includes header navigation

**Error Handling**:
- 500 if database query fails
- 500 if HTML generation fails

**Example Request**:
```
GET /profile
```

**Response**: HTML page with full profile content

---

## HTML Generation

The profile HTML is **generated dynamically from the database** using `profile_generator.py`.

### Generation Process

1. **Query Database**: Retrieves all genes, SNPs, genotypes, traits, health conditions, and citations
2. **Build Document Structure**: Organizes data by gene sections
3. **Format Citations**: Transforms citation numbers to clickable links
4. **Generate HTML**: Creates HTML markup with proper structure
5. **Render Template**: Wraps content in `templates/profile.html` with navigation

### Citation Conversion

```python
def convert_citations(text):
    """Convert [1,2,3] to clickable links"""
    pattern = r'\[(\d+(?:,\s*\d+)*)\]'
    # Creates: <a href="#ref-1"><span class="cite-num">1</span></a>
```

### Reference Anchors

```python
def add_reference_anchors(html_content):
    """Add id="ref-{number}" to list items"""
    # <li id="ref-1">1. Citation text...</li>
```

---

## Citation Links

Citations in the document are clickable and link to the references section.

### Link Format

```html
<sup class="citation">
    <a href="#ref-1" class="cite-link">
        <span class="cite-num">1</span>
    </a>
</sup>
```

### Reference Format

```html
<li id="ref-1">1. Author, A. (Year). Title. Journal.</li>
```

### CSS Styling

```css
.cite-num {
    background: #e3f2fd;
    color: #1565c0;
    padding: 2px 4px;
    border-radius: 2px;
    font-weight: 600;
}

.cite-link {
    text-decoration: none;
}

.cite-link:hover {
    text-decoration: underline;
}

ol > li[id^="ref-"] {
    scroll-margin-top: 80px; /* Smooth scroll offset */
}
```

---

## Template Structure

### Base Template

```html
{% extends "base.html" %}
```

### Profile Template

```html
{% block content %}
<div class="page-header">
    <h2>Full Genetic Profile</h2>
    <p class="page-description">Complete genetic profile document...</p>
</div>

<div class="profile-content">
    {{ profile_html|safe }}
</div>
{% endblock %}
```

### Content Sections

The profile includes:

1. **Header**: Test provider, version, primary sources
2. **Table of Contents**: Links to all gene sections
3. **17 Gene Sections**: Each with:
   - Genotype and SNP information
   - Trait associations
   - Health condition associations
   - Database sources
   - Gene-gene interactions
   - Research findings
4. **Pharmacogenomic Section**: Drug metabolism information
5. **Gene-Gene Interaction Networks**: Summary of interactions
6. **Summary by Category**: Key genes grouped by trait type
7. **References**: All citations (164 total)

---

## Styling

### Profile Content Styles

```css
.profile-content {
    background: white;
    padding: 30px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    max-width: 900px;
    margin: 0 auto;
}

.profile-content h1 {
    font-size: 2em;
    color: #000;
    margin-bottom: 20px;
    padding-bottom: 10px;
    border-bottom: 2px solid #000;
}

.profile-content h2 {
    font-size: 1.5em;
    color: #000;
    margin-top: 40px;
    margin-bottom: 15px;
    padding-bottom: 8px;
    border-bottom: 1px solid #ccc;
}
```

### Typography

- **Font**: System font stack (-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto)
- **Line Height**: 1.6 for readability
- **Max Width**: 900px for optimal reading width
- **Spacing**: Generous margins and padding

---

## Error Handling

### Database Connection Errors

```python
try:
    db = get_db()
    profile_html = generate_profile_html(db)
except Exception as e:
    logger.error(f"Error generating profile from database: {e}")
    return f"Error generating profile: {str(e)}", 500
```

### Generation Errors

```python
try:
    profile_html = generate_profile_html(db)
    if not profile_html or len(profile_html.strip()) < 100:
        return "Profile content is missing. Please check database.", 500
except Exception as e:
    logger.error(f"Error generating profile: {e}", exc_info=True)
    return f"Error generating profile: {str(e)}", 500
```

### Template Errors

Flask will catch template rendering errors and return 500 with error details (in debug mode).

---

## Data Updates

The profile is **always up-to-date** because it's generated directly from the database. 

### Updating Profile Content

To update the profile, modify the database:

```bash
# Import new data from markdown
python3 scripts/import_from_markdown.py

# Add new genes, traits, or conditions via database API
# The profile will automatically reflect changes on next page load
```

**No regeneration needed** - the profile is generated fresh from the database on every request.

---

## Related Files

### Templates
- `templates/base.html` - Base template with header/footer
- `templates/profile.html` - Profile page template

### Scripts
- `scripts/generate_html.py` - HTML generation script

### Source Files
- `genetic_profile.db` - Database (source of all data)
- `profile_generator.py` - Database-to-HTML generator

### Python
- `app.py` - Profile route handler

---

## Debugging

### Profile Not Displaying

1. **Check file exists**:
   ```bash
   ls -la output/genetic_profile.html
   ```

2. **Regenerate HTML**:
   ```bash
   python3 scripts/generate_html.py
   ```

3. **Check server logs**:
   ```bash
   tail -f logs/app.log
   ```

### Citations Not Clickable

1. **Verify citation conversion**:
   - Check HTML source for `<a href="#ref-1">` links
   - Verify reference list has `id="ref-1"` attributes

2. **Check CSS**:
   - Verify `.cite-link` styles are loaded
   - Check for CSS conflicts

### Styling Issues

1. **Inspect element** in browser DevTools
2. **Check CSS specificity** - profile styles may be overridden
3. **Verify template inheritance** - ensure base.html styles are loaded

---

## Future Enhancements

- [ ] Search functionality within profile
- [ ] Print-friendly stylesheet
- [ ] PDF export
- [ ] Section navigation sidebar
- [ ] Highlight search terms
- [ ] Copy citation links
- [ ] Share specific sections
- [ ] Dark mode support

