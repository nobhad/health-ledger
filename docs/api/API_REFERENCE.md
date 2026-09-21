# API Reference

**Last Updated**: December 7, 2025

## Overview

Complete reference for all API endpoints in the Genetic Profile Database application. All endpoints return JSON and support CORS for cross-origin requests.

**Base URL**: `http://localhost:5001`

---

## Table of Contents

- [Health Check](#health-check)
- [Gene Endpoints](#gene-endpoints)
- [Trait Endpoints](#trait-endpoints)
- [Condition Endpoints](#condition-endpoints)
- [Pharmacogenomic Endpoints](#pharmacogenomic-endpoints)
- [Error Handling](#error-handling)
- [Response Formats](#response-formats)

---

## Health Check

### GET /test

Simple health check endpoint to verify server is running.

**Response:**

```json
{
    "status": "ok",
    "message": "Server is working!",
    "version": "1.0.0"
}
```

**Example:**

```bash
curl http://localhost:5001/test
```

---

## Gene Endpoints

### GET /api/all-genes

Get all genes in the database.

**Response:**

```json
[
    {
        "id": 1,
        "gene_symbol": "ADRA2A",
        "gene_name": "Adrenergic Alpha-2A Receptor",
        "chromosome": "10"
    },
    {
        "id": 2,
        "gene_symbol": "COMT",
        "gene_name": "Catechol-O-Methyltransferase",
        "chromosome": "22"
    }
]
```

**Example:**

```bash
curl http://localhost:5001/api/all-genes
```

### GET /api/gene-info

Get comprehensive information about a specific gene.

**Query Parameters:**

- `gene` (required): Gene symbol (e.g., "COMT", "ADRA2A")

**Response:**

```json
{
    "gene_symbol": "COMT",
    "gene_name": "Catechol-O-Methyltransferase",
    "chromosome": "22",
    "traits": [
        "pain sensitivity",
        "stress response"
    ],
    "health_conditions": [
        "ADHD",
        "Anxiety"
    ],
    "interacting_genes": [
        "ADRA2A",
        "HTR2A"
    ],
    "pharmacogenomic": {
        "metabolism_status": "Normal",
        "genotype_phenotype": "Val/Met",
        "affected_medications": "Levodopa, Methyldopa"
    }
}
```

**Example:**

```bash
curl "http://localhost:5001/api/gene-info?gene=COMT"
```

**Error Responses:**

- `400`: Missing gene parameter
- `404`: Gene not found
- `500`: Server error

---

## Trait Endpoints

### GET /api/all-traits

Get all unique traits in the database.

**Response:**

```json
[
    "pain sensitivity",
    "stress response",
    "ADHD susceptibility"
]
```

**Example:**

```bash
curl http://localhost:5001/api/all-traits
```

### GET /api/genes-by-trait

Get genes associated with a specific trait.

**Query Parameters:**

- `trait` (required): Trait name (e.g., "pain sensitivity")

**Response:**

```json
[
    {
        "gene_symbol": "COMT",
        "gene_name": "Catechol-O-Methyltransferase",
        "trait_name": "pain sensitivity",
        "association_direction": "increased"
    }
]
```

**Example:**

```bash
curl "http://localhost:5001/api/genes-by-trait?trait=pain+sensitivity"
```

**Error Responses:**

- `400`: Missing trait parameter
- `500`: Server error

---

## Condition Endpoints

### GET /api/all-conditions

Get all unique health conditions in the database.

**Response:**

```json
[
    "ADHD",
    "Anxiety",
    "Depression",
    "POTS"
]
```

**Example:**

```bash
curl http://localhost:5001/api/all-conditions
```

### GET /api/genes-by-condition

Get genes associated with a specific health condition.

**Query Parameters:**

- `condition` (required): Condition name (e.g., "ADHD")

**Response:**

```json
[
    {
        "gene_symbol": "ADRA2A",
        "gene_name": "Adrenergic Alpha-2A Receptor",
        "condition_name": "ADHD",
        "association_type": "susceptibility"
    }
]
```

**Example:**

```bash
curl "http://localhost:5001/api/genes-by-condition?condition=ADHD"
```

**Error Responses:**

- `400`: Missing condition parameter
- `500`: Server error

---

## Pharmacogenomic Endpoints

### GET /api/pharmacogenomic

Get all pharmacogenomic data.

**Response:**

```json
[
    {
        "gene_symbol": "CYP2D6",
        "gene_name": "Cytochrome P450 2D6",
        "metabolism_status": "Intermediate Metabolizer",
        "genotype_phenotype": "*1/*4",
        "affected_medications": "Citalopram, Venlafaxine, Codeine"
    },
    {
        "gene_symbol": "CYP2C19",
        "gene_name": "Cytochrome P450 2C19",
        "metabolism_status": "Normal Metabolizer",
        "genotype_phenotype": "*1/*1",
        "affected_medications": "Citalopram, Escitalopram"
    }
]
```

**Example:**

```bash
curl http://localhost:5001/api/pharmacogenomic
```

---

## Error Handling

### Error Response Format

All errors return JSON in this format:

```json
{
    "error": "Error message here",
    "status": 400,
    "details": {
        "traceback": "..."  // Only in DEBUG mode
    }
}
```

### HTTP Status Codes

- `200`: Success
- `400`: Bad Request (missing/invalid parameters)
- `404`: Not Found (resource doesn't exist)
- `500`: Internal Server Error (server/database error)

### Input Validation

All API endpoints validate input parameters:

**Gene Symbols:**

- Must be alphanumeric with dashes/underscores
- Maximum 20 characters
- Case-insensitive (automatically converted to uppercase)
- Examples: `COMT`, `ADRA2A`, `CYP2D6`

**Condition/Trait Names:**

- Must be strings
- Maximum 200 characters
- Cannot contain HTML tags (`<`, `>`)
- Examples: `ADHD`, `pain sensitivity`, `stress response`

**List Parameters:**

- Can be single string or array
- Maximum 50 items per query
- Each item validated individually
- Examples: `condition=ADHD` or `condition[]=ADHD&condition[]=Anxiety`

### Example Error Responses

**Missing Parameter:**

```json
{
    "error": "Missing required parameter: condition",
    "status": 400
}
```

**Invalid Parameter:**

```json
{
    "error": "Invalid gene symbol: Gene symbol must be a string",
    "status": 400
}
```

**Not Found:**

```json
{
    "error": "Gene COMTX not found",
    "status": 404
}
```

**Server Error:**

```json
{
    "error": "Internal server error",
    "status": 500,
    "details": {
        "traceback": "Traceback (most recent call last):\n..."
    }
}
```

**Validation Error:**

```json
{
    "error": "Invalid condition: Condition name contains invalid characters",
    "status": 400
}
```

---

## Response Formats

### Array Responses

Endpoints that return lists always return arrays, even if empty:

```json
[]
```

### Object Responses

Endpoints that return single items return objects:

```json
{
    "key": "value"
}
```

### Null Values

Missing or null values are represented as `null`:

```json
{
    "chromosome": null,
    "pharmacogenomic": null
}
```

---

## CORS Support

All endpoints support CORS (Cross-Origin Resource Sharing) for browser-based requests.

**Headers:**

```text
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, OPTIONS
Access-Control-Allow-Headers: Content-Type
```

---

## Rate Limiting

Currently no rate limiting is implemented. For production, consider:

- Request rate limiting
- API key authentication
- Request throttling

---

## Logging

All API requests are logged with:

- Request method and path
- Query parameters
- Response status
- Error details (if any)

**Log Location**: `logs/app.log`

---

## Testing

### Using curl

```bash
# Test health check
curl http://localhost:5001/test

# Get all genes
curl http://localhost:5001/api/all-genes

# Get gene info
curl "http://localhost:5001/api/gene-info?gene=COMT"

# Get genes by condition
curl "http://localhost:5001/api/genes-by-condition?condition=ADHD"
```

### Using Python

```python
import requests

# Get all genes
response = requests.get('http://localhost:5001/api/all-genes')
genes = response.json()
print(f"Found {len(genes)} genes")

# Get gene info
response = requests.get('http://localhost:5001/api/gene-info', 
                       params={'gene': 'COMT'})
gene_info = response.json()
print(gene_info)
```

### Using JavaScript

```javascript
// Get all genes
fetch('/api/all-genes')
    .then(response => response.json())
    .then(data => {
        console.log('Genes:', data);
    })
    .catch(error => {
        console.error('Error:', error);
    });

// Get gene info
fetch('/api/gene-info?gene=COMT')
    .then(response => response.json())
    .then(data => {
        console.log('Gene info:', data);
    });
```

---

## Future Endpoints

Planned endpoints:

- `POST /api/query` - Advanced query endpoint
- `GET /api/citations` - Get all citations
- `GET /api/interactions` - Get gene-gene interactions
- `POST /api/export` - Export data in various formats
- `GET /api/statistics` - Database statistics

---

## Related Files

### Python

- `app.py` - All route handlers
- `database_manager.py` - Database operations

### Documentation

- `docs/DEBUGGING_GUIDE.md` - Debugging API issues
- `docs/features/QUERY_INTERFACE.md` - Query interface using API
