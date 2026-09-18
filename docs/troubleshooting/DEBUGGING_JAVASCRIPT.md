# JavaScript Debugging Guide

**Last Updated**: December 7, 2025

## Overview

Comprehensive debugging utilities and logging for the Genetic Profile Database JavaScript code. All debugging output appears in the browser console with clear prefixes and timestamps.

---

## Quick Start

### Enable Debugging

Debugging is enabled by default. To disable:

```javascript
// In browser console
window.GENETIC_PROFILE_DEBUG.enabled = false;
```

### View Debug Logs

1. Open browser DevTools (F12)
2. Go to Console tab
3. Look for logs prefixed with `[DEBUG]`, `[INFO]`, `[WARN]`, `[ERROR]`

### Filter Browser Extension Errors

The error you're seeing (`content_script.js:1`) is from a browser extension, not our code. To filter it:

**Chrome DevTools:**
1. Open Console
2. Click filter icon
3. Add filter: `-content_script.js`
4. Or use: `Hide network messages` to reduce noise

**Or use console filter:**
```javascript
// In console, filter out extension errors
console.log = (function(originalLog) {
    return function(...args) {
        if (!args[0] || !args[0].includes('content_script.js')) {
            originalLog.apply(console, args);
        }
    };
})(console.log);
```

---

## Debug Logging System

### Log Levels

- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARN**: Warning messages
- **ERROR**: Error messages with stack traces

### Log Format

All logs include:
- Timestamp (ISO format)
- Log level prefix
- Message
- Additional data (if provided)

**Example:**
```
[2025-12-07T21:15:00.123Z DEBUG] loadGenes() called
[2025-12-07T21:15:00.456Z DEBUG] Fetching /api/all-genes
[2025-12-07T21:15:00.789Z INFO] Received 12 genes
```

---

## Debug Functions

### debugLog(message, ...args)

Logs debug information.

```javascript
debugLog('Function called', { param1: 'value1' });
// Output: [DEBUG] Function called { param1: 'value1' }
```

### infoLog(message, ...args)

Logs informational messages.

```javascript
infoLog('Data loaded', { count: 17 });
// Output: [INFO] Data loaded { count: 17 }
```

### warnLog(message, ...args)

Logs warnings.

```javascript
warnLog('Missing data', { field: 'gene_name' });
// Output: [WARN] Missing data { field: 'gene_name' }
```

### errorLog(message, error, ...args)

Logs errors with stack traces.

```javascript
try {
    // code
} catch (error) {
    errorLog('Failed to load data', error);
    // Output: [ERROR] Failed to load data Error: ...
    //         Stack trace: ...
}
```

### perfLog(operation, startTime)

Logs performance metrics.

```javascript
const start = performance.now();
// ... operation ...
perfLog('loadGenes', start);
// Output: [PERF] loadGenes: 123.45ms (colored by duration)
```

### apiLog(method, url, data, response)

Logs API calls with request/response.

```javascript
apiLog('GET', '/api/all-genes', null, responseData);
// Output: 🌐 API GET /api/all-genes
//         📥 Response: [...]
```

---

## Common Debugging Scenarios

### 1. API Calls Not Working

**Check logs:**
```javascript
// Look for these in console:
[DEBUG] Fetching /api/all-genes
[DEBUG] Response received { status: 200, ok: true }
[ERROR] Error loading genes Error: ...
```

**Debug steps:**
1. Check network tab for failed requests
2. Verify API endpoint is correct
3. Check response status code
4. Verify response is JSON array

### 2. Multiselect Not Showing Options

**Check logs:**
```javascript
[DEBUG] initMultiselect() called { type: 'gene', ... }
[DEBUG] Elements found { input: true, dropdown: true, tags: true }
[DEBUG] State for gene { options: [], selected: [] }
[WARN] No options available for gene, showing loading message
```

**Debug steps:**
1. Verify `loadGenes()` completed successfully
2. Check `multiselectState.genes.options` has data
3. Verify DOM elements exist
4. Check for JavaScript errors

### 3. Results Not Displaying

**Check logs:**
```javascript
[DEBUG] showResults() called { title: '...', dataLength: 5 }
[DEBUG] Displaying 5 results
[ERROR] Results element not found
```

**Debug steps:**
1. Verify `results` element exists in DOM
2. Check data format (should be array)
3. Verify `showResults()` is called
4. Check for HTML generation errors

---

## Debugging Tools

### Browser Console

**Access:**
- Chrome/Edge: F12 → Console
- Firefox: F12 → Console
- Safari: Cmd+Option+C

**Useful Commands:**
```javascript
// Check multiselect state
console.log(multiselectState);

// Check if elements exist
console.log(document.getElementById('geneInput'));
console.log(document.getElementById('geneDropdown'));

// Test API endpoint
fetch('/api/all-genes')
    .then(r => r.json())
    .then(data => console.log('Genes:', data))
    .catch(err => console.error('Error:', err));

// Check state for specific type
console.log('Gene options:', multiselectState.genes.options);
console.log('Selected genes:', multiselectState.genes.selected);
```

### Network Tab

**Check:**
- API requests (status codes, response data)
- Request/response headers
- Timing information
- Failed requests (red entries)

### Elements Tab

**Inspect:**
- Multiselect DOM structure
- CSS classes and styles
- Event listeners
- Element visibility

---

## Performance Debugging

### Measure Function Performance

```javascript
const start = performance.now();
await loadGenes();
perfLog('loadGenes', start);
```

### Monitor API Response Times

All API calls are automatically logged with timing:
```
[DEBUG] loadGenes() called
[DEBUG] loadGenes() completed in 123.45ms
```

### Check for Slow Operations

Look for logs with high duration:
```
[PERF] loadGenes: 5000.00ms  // ⚠️ Slow!
```

---

## Error Handling

### Try-Catch Blocks

All async functions include try-catch:

```javascript
async function loadGenes() {
    try {
        // ... code ...
    } catch (error) {
        errorLog('Error loading genes', error);
        // Error logged with full stack trace
    }
}
```

### Error Display

Errors are displayed in UI and logged to console:

```javascript
// UI error display
document.getElementById('results').innerHTML = 
    '<div class="error">Error: ' + error.message + '</div>';

// Console error log
errorLog('Error in queryByCondition', error);
```

---

## Debug Configuration

### Global Configuration

```javascript
// Access configuration
window.GENETIC_PROFILE_DEBUG

// Properties:
{
    enabled: true,           // Enable/disable all logging
    logLevel: 'DEBUG',       // Minimum log level
    showTimestamps: true,    // Show timestamps
    showStackTraces: true    // Show error stack traces
}
```

### Change Log Level

```javascript
// In browser console
window.GENETIC_PROFILE_DEBUG.logLevel = 'INFO';  // Only INFO, WARN, ERROR
window.GENETIC_PROFILE_DEBUG.logLevel = 'WARN';  // Only WARN, ERROR
window.GENETIC_PROFILE_DEBUG.logLevel = 'ERROR'; // Only ERROR
```

### Disable Debugging

```javascript
// Disable all debug logs
window.GENETIC_PROFILE_DEBUG.enabled = false;
```

---

## Filtering Console Output

### Filter by Prefix

**Chrome DevTools:**
1. Console → Filter icon
2. Enter: `[DEBUG]` or `[ERROR]`
3. Only matching logs shown

### Filter Out Extension Errors

**Add to console filter:**
```
-content_script.js -installHook.js
```

**Or use negative filter:**
```
-[extension]
```

### Custom Filter Function

```javascript
// In console
const originalLog = console.log;
console.log = function(...args) {
    const message = args[0];
    if (message && (
        message.includes('[DEBUG]') ||
        message.includes('[ERROR]') ||
        message.includes('[WARN]')
    )) {
        originalLog.apply(console, args);
    }
};
```

---

## Debugging Checklist

When debugging an issue:

- [ ] Check browser console for errors
- [ ] Verify API endpoints are responding
- [ ] Check network tab for failed requests
- [ ] Verify DOM elements exist
- [ ] Check multiselect state
- [ ] Verify data format (arrays vs objects)
- [ ] Check for JavaScript syntax errors
- [ ] Verify event listeners are attached
- [ ] Check CSS (z-index, visibility, display)
- [ ] Test with minimal data

---

## Common Issues

### 1. "Cannot read properties of undefined"

**Cause**: Object/array not initialized

**Solution**: Check initialization:
```javascript
// Verify state exists
if (!multiselectState[type]) {
    multiselectState[type] = { options: [], selected: [] };
}
```

### 2. "Response is not an array"

**Cause**: API returned error object instead of array

**Solution**: Check response:
```javascript
const data = await response.json();
if (!Array.isArray(data)) {
    errorLog('Response is not an array', null, { data });
    return;
}
```

### 3. "Element not found"

**Cause**: DOM element doesn't exist or wrong ID

**Solution**: Verify element exists:
```javascript
const element = document.getElementById('geneInput');
if (!element) {
    errorLog('Element not found', null, { id: 'geneInput' });
    return;
}
```

---

## Related Files

### JavaScript
- `static/js/debug.js` - Debug utilities
- `static/js/query.js` - Query functions with logging
- `static/js/multiselect.js` - Multiselect with logging

### Documentation
- `docs/DEBUGGING_GUIDE.md` - General debugging guide
- `docs/features/QUERY_INTERFACE.md` - Query interface docs

---

## Quick Reference

### Enable Debug Panel (Optional)

```javascript
// In browser console
window.initDebugPanel();
```

Shows a floating debug panel with controls.

### Check Application State

```javascript
// In browser console
console.log('Multiselect State:', multiselectState);
console.log('Debug Config:', window.GENETIC_PROFILE_DEBUG);
```

### Test API Endpoints

```javascript
// In browser console
fetch('/api/all-genes')
    .then(r => r.json())
    .then(data => {
        console.log('✅ API working:', data.length, 'genes');
    })
    .catch(err => {
        console.error('❌ API error:', err);
    });
```

