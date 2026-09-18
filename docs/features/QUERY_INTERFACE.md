# Query Interface Feature

**Last Updated**: December 7, 2025

## Overview

The Query Interface is the main entry point for searching and exploring genetic profile data. It provides searchable multiselect dropdowns for genes, traits, and health conditions, allowing users to find associations and relationships in their genetic data.

**Key Features:**

- 🔍 Searchable multiselect dropdowns for genes, traits, and conditions
- 📊 Real-time query results displayed in tables
- 🔗 Quick actions for common queries
- 📱 Responsive design for all devices

---

## Table of Contents

- [User Interface](#user-interface)
- [Search Functionality](#search-functionality)
- [Query Types](#query-types)
- [API Endpoints](#api-endpoints)
- [JavaScript Components](#javascript-components)
- [Error Handling](#error-handling)
- [Performance Considerations](#performance-considerations)
- [Related Files](#related-files)

---

## User Interface

### Layout

The query interface is organized into cards:

1. **Find Genes by Health Condition** - Search for genes associated with specific health conditions
2. **Find Genes by Trait** - Search for genes associated with traits
3. **Get Gene Information** - Get comprehensive information about specific genes
4. **Quick Actions** - Common queries (all genes, pharmacogenomic data)

### Multiselect Dropdowns

Each search field uses a custom multiselect component that supports:

- **Type-to-search**: Filter options as you type
- **Multiple selection**: Select multiple items with checkboxes
- **Tag display**: Selected items shown as removable tags
- **Keyboard navigation**: Arrow keys, Enter, Escape support

**Example:**
```html
<div class="multiselect-wrapper" id="conditionMultiselect">
    <div class="multiselect-tags" id="conditionTags"></div>
    <input type="text" class="multiselect-input" id="conditionInput" 
           placeholder="Click here or type to search conditions...">
    <div class="multiselect-dropdown" id="conditionDropdown"></div>
</div>
```

---

## Search Functionality

### Loading Options

On page load, the interface fetches all available options:

```javascript
// Load genes
async function loadGenes() {
    const response = await fetch('/api/all-genes');
    const data = await response.json();
    multiselectState.genes.options = data.map(gene => ({
        value: gene.gene_symbol,
        label: gene.gene_symbol + ' - ' + (gene.gene_name || '')
    }));
}

// Load conditions
async function loadConditions() {
    const response = await fetch('/api/all-conditions');
    const data = await response.json();
    multiselectState.conditions.options = data.map(condition => ({
        value: condition,
        label: condition
    }));
}

// Load traits
async function loadTraits() {
    const response = await fetch('/api/all-traits');
    const data = await response.json();
    multiselectState.traits.options = data.map(trait => ({
        value: trait,
        label: trait
    }));
}
```

### Filtering

Options are filtered in real-time as the user types:

```javascript
function updateMultiselectDropdown(type, filter = '') {
    const filterLower = filter.toLowerCase();
    const filtered = state.options.filter(option => 
        option.label.toLowerCase().includes(filterLower)
    );
    // Display filtered options
}
```

### Performance Optimization

- **Limit visible options**: Maximum 50 options shown at once
- **Lazy loading**: Options loaded on demand
- **Debouncing**: Filter updates debounced for performance

---

## Query Types

### 1. Query by Health Condition

**Purpose**: Find all genes associated with one or more health conditions.

**Usage:**
1. Select one or more health conditions from the dropdown
2. Click "Search" button
3. Results show genes associated with selected conditions

**Example Query:**
```javascript
queryByCondition() {
    const selected = ['ADHD', 'Anxiety'];
    // Fetches: /api/genes-by-condition?condition=ADHD
    //          /api/genes-by-condition?condition=Anxiety
    // Combines and deduplicates results
}
```

**Response Format:**
```json
[
    {
        "gene_symbol": "ADRA2A",
        "gene_name": "Adrenergic Alpha-2A Receptor",
        "condition_name": "ADHD"
    }
]
```

### 2. Query by Trait

**Purpose**: Find all genes associated with one or more traits.

**Usage:**
1. Select one or more traits from the dropdown
2. Click "Search" button
3. Results show genes associated with selected traits

**Example Query:**
```javascript
queryByTrait() {
    const selected = ['pain sensitivity', 'stress response'];
    // Fetches: /api/genes-by-trait?trait=pain+sensitivity
    //          /api/genes-by-trait?trait=stress+response
    // Combines and deduplicates results
}
```

### 3. Query Gene Information

**Purpose**: Get comprehensive information about specific genes.

**Usage:**
1. Select one or more genes from the dropdown
2. Click "Get Gene Info" button
3. Results show detailed information for each gene

**Response Format:**
```json
{
    "gene_symbol": "COMT",
    "gene_name": "Catechol-O-Methyltransferase",
    "chromosome": "22",
    "traits": ["pain sensitivity", "stress response"],
    "health_conditions": ["ADHD", "Anxiety"],
    "interacting_genes": ["ADRA2A", "HTR2A"],
    "pharmacogenomic": {
        "metabolism_status": "Normal",
        "genotype_phenotype": "Val/Val",
        "affected_medications": "Levodopa, Methyldopa"
    }
}
```

### 4. Quick Actions

**Show All Genes:**
- Displays all genes in the database
- Endpoint: `/api/all-genes`

**Show Medication Metabolism:**
- Displays pharmacogenomic data for all genes
- Endpoint: `/api/pharmacogenomic`

---

## API Endpoints

### GET /api/all-genes

Returns all genes in the database.

**Response:**
```json
[
    {
        "id": 1,
        "gene_symbol": "ADRA2A",
        "gene_name": "Adrenergic Alpha-2A Receptor",
        "chromosome": "10"
    }
]
```

### GET /api/all-conditions

Returns all unique health conditions.

**Response:**
```json
["ADHD", "Anxiety", "Depression", ...]
```

### GET /api/all-traits

Returns all unique traits.

**Response:**
```json
["pain sensitivity", "stress response", ...]
```

### GET /api/genes-by-condition

**Query Parameters:**
- `condition` (required): Health condition name

**Response:**
```json
[
    {
        "gene_symbol": "ADRA2A",
        "gene_name": "...",
        "condition_name": "ADHD"
    }
]
```

### GET /api/genes-by-trait

**Query Parameters:**
- `trait` (required): Trait name

**Response:**
```json
[
    {
        "gene_symbol": "COMT",
        "gene_name": "...",
        "trait_name": "pain sensitivity"
    }
]
```

### GET /api/gene-info

**Query Parameters:**
- `gene` (required): Gene symbol (e.g., "COMT")

**Response:**
See [Query Gene Information](#3-query-gene-information) section.

---

## JavaScript Components

### Multiselect State Management

```javascript
const multiselectState = {
    conditions: { options: [], selected: [] },
    traits: { options: [], selected: [] },
    genes: { options: [], selected: [] }
};
```

### Key Functions

**initMultiselect(type, inputId, dropdownId, tagsId)**
- Initializes a multiselect component
- Sets up event listeners
- Configures dropdown behavior

**updateMultiselectDropdown(type, filter)**
- Updates dropdown with filtered options
- Handles selection state
- Limits display to 50 items for performance

**toggleMultiselectOption(type, value)**
- Toggles selection of an option
- Updates tags display
- Refreshes dropdown

**showResults(data, title)**
- Displays query results in a table
- Handles empty results
- Formats data for display

---

## Error Handling

### Client-Side Errors

```javascript
try {
    const response = await fetch('/api/genes-by-condition?condition=ADHD');
    const data = await response.json();
    
    if (!Array.isArray(data)) {
        console.error('Error: Response is not an array', data);
        return;
    }
    
    showResults(data, 'Genes Associated with: ADHD');
} catch (error) {
    hideLoading();
    document.getElementById('results').innerHTML = 
        '<div class="error">Error: ' + error.message + '</div>';
}
```

### Server-Side Errors

All API endpoints return consistent error format:

```json
{
    "error": "Error message",
    "traceback": "..." // Only in DEBUG mode
}
```

**Error Codes:**
- `400`: Bad Request (missing/invalid parameters)
- `404`: Not Found (gene/condition/trait not found)
- `500`: Internal Server Error (server/database error)

---

## Performance Considerations

### Optimization Strategies

1. **Limit API Calls**: Combine multiple selections into single queries where possible
2. **Deduplicate Results**: Remove duplicate genes from combined queries
3. **Lazy Loading**: Load options on demand, not all at once
4. **Pagination**: Consider pagination for large result sets
5. **Caching**: Cache frequently accessed data

### Current Limits

- Maximum 50 options shown in dropdown at once
- Results displayed in tables (consider pagination for 100+ results)
- API responses limited to reasonable sizes

---

## Related Files

### Templates
- `templates/query.html` - Main query interface template
- `templates/components.html` - Reusable UI components

### JavaScript
- `static/js/multiselect.js` - Multiselect component logic
- `static/js/query.js` - Query functions and API calls

### CSS
- `static/css/style.css` - Styling for query interface

### Python
- `app.py` - API route handlers
- `database_manager.py` - Database query methods

---

## Debugging

### Common Issues

1. **Dropdowns not showing options**
   - Check browser console for API errors
   - Verify API endpoints are returning arrays
   - Check network tab for failed requests

2. **Selected items not persisting**
   - Verify `multiselectState` is properly initialized
   - Check for JavaScript errors in console
   - Ensure event listeners are attached

3. **Results not displaying**
   - Check `showResults()` function
   - Verify data format matches expected structure
   - Check for JavaScript errors

### Debug Commands

```javascript
// In browser console
console.log(multiselectState);
console.log(multiselectState.genes.options);
console.log(multiselectState.genes.selected);

// Test API endpoint
fetch('/api/all-genes')
    .then(r => r.json())
    .then(data => console.log(data));
```

---

## Future Enhancements

- [ ] Add pagination for large result sets
- [ ] Implement result export (CSV, JSON)
- [ ] Add advanced filtering options
- [ ] Support for saved queries
- [ ] Query history
- [ ] Result comparison tools
- [ ] Visualization charts for gene relationships

