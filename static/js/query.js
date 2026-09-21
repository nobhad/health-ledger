"use strict";
/**
 * Query interface for Health Ledger
 * Handles API calls and result display
 */
// Ensure debug functions are available
if (typeof window.debugLog === 'undefined') {
    window.debugLog = function (message, ...args) {
        console.log(`[QUERY DEBUG] ${message}`, ...args);
    };
}
if (typeof window.errorLog === 'undefined') {
    window.errorLog = function (message, error, ...args) {
        console.error(`[QUERY ERROR] ${message}`, error, ...args);
        if (error && error.stack) {
            console.error('Stack trace:', error.stack);
        }
    };
}
if (typeof window.warnLog === 'undefined') {
    window.warnLog = function (message, ...args) {
        console.warn(`[QUERY WARN] ${message}`, ...args);
    };
}
// Use window functions directly - no local const declarations
// This avoids "already declared" errors
// Load genes, conditions, and traits on page load
document.addEventListener('DOMContentLoaded', function () {
    console.log('%c[INIT] DOM Content Loaded - Starting application initialization', 'color: #0066cc; font-weight: bold');
    window.debugLog('DOM Content Loaded - Initializing application');
    try {
        // Initialize multiselects first (with empty state)
        console.log('%c[INIT] Initializing multiselect components...', 'color: #0066cc');
        window.debugLog('Initializing multiselect components');
        if (window.initMultiselect) {
            window.initMultiselect('condition', 'conditionInput', 'conditionDropdown', 'conditionTags');
            window.initMultiselect('trait', 'traitInput', 'traitDropdown', 'traitTags');
            window.initMultiselect('gene', 'geneInput', 'geneDropdown', 'geneTags');
        }
        // Initialize Lucide icons
        if (typeof window.lucide !== 'undefined') {
            window.lucide.createIcons();
        }
        console.log('%c[INIT] [OK] Multiselect components initialized', 'color: #28a745; font-weight: bold');
        window.debugLog('Multiselect components initialized');
        // Then load data
        console.log('%c[INIT] Loading data from API...', 'color: #0066cc');
        window.debugLog('Loading data from API');
        loadGenes();
        loadConditions();
        loadTraits();
        console.log('%c[INIT] [OK] Application initialization complete', 'color: #28a745; font-weight: bold');
    }
    catch (error) {
        console.error('%c[INIT] [ERROR] Error during initialization', 'color: #dc3545; font-weight: bold', error);
        window.errorLog('Error during initialization', error);
    }
});
async function loadGenes() {
    console.log('%c[API] loadGenes() called', 'color: #17a2b8');
    window.debugLog('loadGenes() called');
    const startTime = performance.now();
    try {
        console.log('%c[API] Fetching /api/all-genes...', 'color: #17a2b8');
        window.debugLog('Fetching /api/all-genes');
        const response = await fetch('/api/all-genes');
        console.log('%c[API] Response received', 'color: #17a2b8', {
            status: response.status,
            statusText: response.statusText,
            ok: response.ok
        });
        window.debugLog('Response received', {
            status: response.status,
            statusText: response.statusText,
            ok: response.ok
        });
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const data = await response.json();
        console.log('%c[API] Response data:', 'color: #17a2b8', {
            type: typeof data,
            isArray: Array.isArray(data),
            length: Array.isArray(data) ? data.length : 'N/A'
        });
        window.debugLog('Response data parsed', { dataType: typeof data, isArray: Array.isArray(data) });
        // Check if response is an array
        if (!Array.isArray(data)) {
            console.error('%c[API] ✗ Error: Response is not an array', 'color: #dc3545; font-weight: bold', data);
            window.errorLog('Error loading genes: Response is not an array', null, { data });
            return;
        }
        console.log(`%c[API] Processing ${data.length} genes`, 'color: #17a2b8');
        window.debugLog(`Processing ${data.length} genes`);
        // Store options for multiselect (use window.multiselectState)
        // IMPORTANT: Use singular keys ('gene', 'condition', 'trait') to match multiselect type parameter
        if (!window.multiselectState) {
            window.multiselectState = {
                condition: { options: [], selected: [] },
                trait: { options: [], selected: [] },
                gene: { options: [], selected: [] }
            };
        }
        if (!window.multiselectState.gene) {
            window.multiselectState.gene = { options: [], selected: [] };
        }
        if (!Array.isArray(window.multiselectState.gene.options)) {
            window.multiselectState.gene.options = [];
        }
        if (!Array.isArray(window.multiselectState.gene.selected)) {
            window.multiselectState.gene.selected = [];
        }
        // Store options as array
        const optionsArray = data.map(gene => ({
            value: gene.gene_symbol,
            label: gene.gene_symbol + ' - ' + (gene.gene_name || '')
        }));
        window.multiselectState.gene.options = optionsArray;
        console.log(`%c[API] ✓ Stored ${window.multiselectState.gene.options.length} gene options`, 'color: #28a745; font-weight: bold');
        window.debugLog(`Stored ${window.multiselectState.gene.options.length} gene options`);
        window.debugLog('State after storing', {
            stateExists: !!window.multiselectState.gene,
            optionsCount: window.multiselectState.gene.options.length,
            optionsIsArray: Array.isArray(window.multiselectState.gene.options),
            optionsType: typeof window.multiselectState.gene.options
        });
        // Verify it's actually stored
        const verifyState = window.multiselectState.gene;
        window.debugLog('Verification check', {
            verifyOptionsCount: verifyState?.options?.length || 0,
            verifyIsArray: Array.isArray(verifyState?.options)
        });
        // Update dropdown - data is now in state
        // Don't show dropdown, just prepare it for when user clicks
        // Use setTimeout to ensure state is fully committed
        setTimeout(() => {
            if (window.updateMultiselectDropdown) {
                window.debugLog('Calling updateMultiselectDropdown for gene after delay', {
                    optionsCount: window.multiselectState?.gene?.options?.length || 0
                });
                window.updateMultiselectDropdown('gene', '');
            }
        }, 0);
        const duration = performance.now() - startTime;
        console.log(`%c[API] ✓ loadGenes() completed in ${duration.toFixed(2)}ms`, 'color: #28a745');
        window.debugLog(`loadGenes() completed in ${duration.toFixed(2)}ms`);
    }
    catch (error) {
        console.error('%c[API] ✗ Error loading genes', 'color: #dc3545; font-weight: bold', error);
        window.errorLog('Error loading genes', error);
    }
}
async function loadConditions() {
    console.log('%c[API] loadConditions() called', 'color: #17a2b8');
    window.debugLog('loadConditions() called');
    const startTime = performance.now();
    try {
        console.log('%c[API] Fetching /api/all-conditions...', 'color: #17a2b8');
        window.debugLog('Fetching /api/all-conditions');
        const response = await fetch('/api/all-conditions');
        console.log('%c[API] Response received', 'color: #17a2b8', {
            status: response.status,
            ok: response.ok
        });
        window.debugLog('Response received', {
            status: response.status,
            statusText: response.statusText,
            ok: response.ok
        });
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const data = await response.json();
        console.log('%c[API] Response data:', 'color: #17a2b8', {
            type: typeof data,
            isArray: Array.isArray(data),
            length: Array.isArray(data) ? data.length : 'N/A'
        });
        window.debugLog('Response data parsed', { dataType: typeof data, isArray: Array.isArray(data) });
        // Check if response is an array
        if (!Array.isArray(data)) {
            console.error('%c[API] ✗ Error: Response is not an array', 'color: #dc3545; font-weight: bold', data);
            window.errorLog('Error loading conditions: Response is not an array', null, { data });
            return;
        }
        console.log(`%c[API] Processing ${data.length} conditions`, 'color: #17a2b8');
        window.debugLog(`Processing ${data.length} conditions`);
        // Store options for multiselect (use window.multiselectState)
        // IMPORTANT: Use singular keys ('gene', 'condition', 'trait') to match multiselect type parameter
        if (!window.multiselectState) {
            window.multiselectState = {
                condition: { options: [], selected: [] },
                trait: { options: [], selected: [] },
                gene: { options: [], selected: [] }
            };
        }
        if (!window.multiselectState.condition) {
            window.multiselectState.condition = { options: [], selected: [] };
        }
        if (!Array.isArray(window.multiselectState.condition.options)) {
            window.multiselectState.condition.options = [];
        }
        if (!Array.isArray(window.multiselectState.condition.selected)) {
            window.multiselectState.condition.selected = [];
        }
        // Store options as array
        const optionsArray = data.map(condition => ({
            value: condition,
            label: condition
        }));
        window.multiselectState.condition.options = optionsArray;
        console.log(`%c[API] ✓ Stored ${window.multiselectState.condition.options.length} condition options`, 'color: #28a745; font-weight: bold');
        window.debugLog(`Stored ${window.multiselectState.condition.options.length} condition options`);
        window.debugLog('State after storing', {
            stateExists: !!window.multiselectState.condition,
            optionsCount: window.multiselectState.condition.options.length,
            optionsIsArray: Array.isArray(window.multiselectState.condition.options)
        });
        // Update dropdown - data is now in state
        // Use setTimeout to ensure state is fully committed
        setTimeout(() => {
            if (window.updateMultiselectDropdown) {
                window.debugLog('Calling updateMultiselectDropdown for condition after delay', {
                    optionsCount: window.multiselectState?.condition?.options?.length || 0
                });
                window.updateMultiselectDropdown('condition', '');
            }
        }, 0);
        const duration = performance.now() - startTime;
        console.log(`%c[API] ✓ loadConditions() completed in ${duration.toFixed(2)}ms`, 'color: #28a745');
        window.debugLog(`loadConditions() completed in ${duration.toFixed(2)}ms`);
    }
    catch (error) {
        console.error('%c[API] ✗ Error loading conditions', 'color: #dc3545; font-weight: bold', error);
        window.errorLog('Error loading conditions', error);
    }
}
async function loadTraits() {
    console.log('%c[API] loadTraits() called', 'color: #17a2b8');
    window.debugLog('loadTraits() called');
    const startTime = performance.now();
    try {
        console.log('%c[API] Fetching /api/all-traits...', 'color: #17a2b8');
        window.debugLog('Fetching /api/all-traits');
        const response = await fetch('/api/all-traits');
        console.log('%c[API] Response received', 'color: #17a2b8', {
            status: response.status,
            ok: response.ok
        });
        window.debugLog('Response received', {
            status: response.status,
            statusText: response.statusText,
            ok: response.ok
        });
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const data = await response.json();
        console.log('%c[API] Response data:', 'color: #17a2b8', {
            type: typeof data,
            isArray: Array.isArray(data),
            length: Array.isArray(data) ? data.length : 'N/A'
        });
        window.debugLog('Response data parsed', { dataType: typeof data, isArray: Array.isArray(data) });
        // Check if response is an array
        if (!Array.isArray(data)) {
            console.error('%c[API] ✗ Error: Response is not an array', 'color: #dc3545; font-weight: bold', data);
            window.errorLog('Error loading traits: Response is not an array', null, { data });
            return;
        }
        console.log(`%c[API] Processing ${data.length} traits`, 'color: #17a2b8');
        window.debugLog(`Processing ${data.length} traits`);
        // Store options for multiselect (use window.multiselectState)
        // IMPORTANT: Use singular keys ('gene', 'condition', 'trait') to match multiselect type parameter
        if (!window.multiselectState) {
            window.multiselectState = {
                condition: { options: [], selected: [] },
                trait: { options: [], selected: [] },
                gene: { options: [], selected: [] }
            };
        }
        if (!window.multiselectState.trait) {
            window.multiselectState.trait = { options: [], selected: [] };
        }
        if (!Array.isArray(window.multiselectState.trait.options)) {
            window.multiselectState.trait.options = [];
        }
        if (!Array.isArray(window.multiselectState.trait.selected)) {
            window.multiselectState.trait.selected = [];
        }
        // Store options as array
        const optionsArray = data.map(trait => ({
            value: trait,
            label: trait
        }));
        window.multiselectState.trait.options = optionsArray;
        console.log(`%c[API] ✓ Stored ${window.multiselectState.trait.options.length} trait options`, 'color: #28a745; font-weight: bold');
        window.debugLog(`Stored ${window.multiselectState.trait.options.length} trait options`);
        window.debugLog('State after storing', {
            stateExists: !!window.multiselectState.trait,
            optionsCount: window.multiselectState.trait.options.length,
            optionsIsArray: Array.isArray(window.multiselectState.trait.options)
        });
        // Update dropdown - data is now in state
        // Use setTimeout to ensure state is fully committed
        setTimeout(() => {
            if (window.updateMultiselectDropdown) {
                window.debugLog('Calling updateMultiselectDropdown for trait after delay', {
                    optionsCount: window.multiselectState?.trait?.options?.length || 0
                });
                window.updateMultiselectDropdown('trait', '');
            }
        }, 0);
        const duration = performance.now() - startTime;
        console.log(`%c[API] ✓ loadTraits() completed in ${duration.toFixed(2)}ms`, 'color: #28a745');
        console.log('%c[INIT] ✓ All data loaded successfully!', 'color: #28a745; font-weight: bold; font-size: 14px');
        window.debugLog(`loadTraits() completed in ${duration.toFixed(2)}ms`);
    }
    catch (error) {
        console.error('%c[API] ✗ Error loading traits', 'color: #dc3545; font-weight: bold', error);
        window.errorLog('Error loading traits', error);
    }
}
function showLoading() {
    window.debugLog('showLoading() called');
    const loadingEl = document.getElementById('loading');
    const resultsEl = document.getElementById('results');
    if (!loadingEl) {
        window.warnLog('Loading element not found');
        return;
    }
    if (!resultsEl) {
        window.warnLog('Results element not found');
        return;
    }
    loadingEl.style.display = 'block';
    resultsEl.innerHTML = '';
    window.debugLog('Loading indicator shown');
}
function hideLoading() {
    window.debugLog('hideLoading() called');
    const loadingEl = document.getElementById('loading');
    if (loadingEl) {
        loadingEl.style.display = 'none';
        window.debugLog('Loading indicator hidden');
    }
    else {
        window.warnLog('Loading element not found');
    }
}
// Global results storage for filtering
if (!window.allResults) {
    window.allResults = [];
}
function showResults(data, title) {
    window.debugLog('showResults() called', { title, dataLength: Array.isArray(data) ? data.length : undefined, hasError: !Array.isArray(data) && 'error' in data });
    const startTime = performance.now();
    hideLoading();
    const resultsEl = document.getElementById('results');
    if (!resultsEl) {
        window.errorLog('Results element not found');
        return;
    }
    if (!Array.isArray(data)) {
        if ('error' in data) {
            window.errorLog('Error in results data', null, { error: data.error });
            resultsEl.innerHTML = '<div class="error">' + escapeHtml(data.error) + '</div>';
        }
        else {
            window.errorLog('Results data is not an array', null, { data });
            resultsEl.innerHTML = '<div class="error">Invalid data format</div>';
        }
        return;
    }
    if (data.length === 0) {
        window.debugLog('No results found');
        resultsEl.innerHTML = '<div class="results"><h2>' + escapeHtml(title) + '</h2><p>No results found.</p></div>';
        return;
    }
    // Store results globally for filtering
    window.allResults = data;
    window.debugLog(`Displaying ${data.length} results in unified filterable view`);
    // Get all unique keys from all items
    const allKeys = new Set();
    data.forEach(item => {
        Object.keys(item).forEach(key => allKeys.add(key));
    });
    const keys = Array.from(allKeys).sort();
    // Build unified filterable table. No wrapper of its own: resultsEl is
    // already .results-container and pads itself, and a second one inside
    // it padded the results twice, so they sat 40px further in than the
    // content on every other page.
    let html = '<div class="results-header">';
    html += '<h2>' + escapeHtml(title) + '</h2>';
    html += '<div class="results-controls">';
    html += '<input type="text" id="resultsFilter" placeholder="Filter results..." class="filter-input" onkeyup="filterResults()">';
    html += '<span class="results-count">Showing <strong id="visibleCount">' + data.length + '</strong> of ' + data.length + ' results</span>';
    html += '</div>';
    html += '</div>';
    html += '<div class="results-table-wrapper">';
    html += '<table class="results-table" id="resultsTable">';
    html += '<thead><tr>';
    keys.forEach(key => {
        const displayKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        html += '<th>' + escapeHtml(displayKey) + '</th>';
    });
    html += '</tr></thead><tbody>';
    data.forEach((item, index) => {
        html += '<tr class="result-row" data-index="' + index + '">';
        keys.forEach(key => {
            let value = item[key];
            if (value === null || value === undefined) {
                value = '';
            }
            // A gene's own variants read as a list, not as JSON in a cell.
            if (key === 'variants' && isVariantList(value)) {
                html += '<td data-search="' + escapeHtml(variantSearchText(value)) + '">'
                    + variantListHtml(value) + '</td>';
                return;
            }
            if (typeof value === 'object' && value !== null) {
                if (Array.isArray(value)) {
                    value = value.join(', ');
                }
                else {
                    try {
                        value = JSON.stringify(value);
                    }
                    catch (e) {
                        value = '[Object]';
                    }
                }
            }
            // Make value searchable
            const searchableValue = String(value).toLowerCase();
            html += '<td data-search="' + escapeHtml(searchableValue) + '">' + escapeHtml(String(value)) + '</td>';
        });
        html += '</tr>';
    });
    html += '</tbody></table>';
    html += '</div>';
    resultsEl.innerHTML = html;
    const duration = performance.now() - startTime;
    window.debugLog(`showResults() completed in ${duration.toFixed(2)}ms`);
}
function isVariantList(value) {
    return Array.isArray(value) && value.length > 0
        && value.every(row => typeof row === 'object' && row !== null && 'rsid' in row);
}
function variantListHtml(variants) {
    const items = variants.map(v => '<li><strong>' + escapeHtml(v.rsid) + '</strong> ' + escapeHtml(v.genotype)
        + (v.description ? ' &middot; ' + escapeHtml(v.description) : '') + '</li>').join('');
    return '<ul class="cell-list">' + items + '</ul>';
}
function variantSearchText(variants) {
    return variants.map(v => v.rsid + ' ' + v.genotype + ' ' + v.description).join(' ').toLowerCase();
}
function escapeHtml(text) {
    if (text === null || text === undefined) {
        return '';
    }
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
}
function filterResults() {
    const filterInput = document.getElementById('resultsFilter');
    const filterValue = filterInput ? filterInput.value.toLowerCase() : '';
    const rows = document.querySelectorAll('#resultsTable tbody tr.result-row');
    let visibleCount = 0;
    rows.forEach(row => {
        const searchableText = row.textContent?.toLowerCase() || '';
        if (searchableText.includes(filterValue)) {
            row.style.display = '';
            visibleCount++;
        }
        else {
            row.style.display = 'none';
        }
    });
    const countEl = document.getElementById('visibleCount');
    if (countEl) {
        countEl.textContent = String(visibleCount);
    }
}
// Make filterResults available globally
window.filterResults = filterResults;
async function queryByCondition() {
    window.debugLog('queryByCondition() called');
    const startTime = performance.now();
    const selected = (window.multiselectState && window.multiselectState.condition) ? window.multiselectState.condition.selected : [];
    window.debugLog('Selected conditions', { selected, count: selected.length });
    if (selected.length === 0) {
        window.warnLog('No conditions selected');
        alert('Please select at least one condition');
        return;
    }
    showLoading();
    try {
        // Query for each condition and combine results
        const allResults = [];
        for (const condition of selected) {
            window.debugLog(`Querying condition: ${condition}`);
            const url = '/api/genes-by-condition?condition=' + encodeURIComponent(condition);
            window.debugLog('Fetching', { url });
            const response = await fetch(url);
            window.debugLog('Response received', {
                condition,
                status: response.status,
                ok: response.ok
            });
            if (!response.ok) {
                throw new Error(`HTTP ${response.status} for condition: ${condition}`);
            }
            const data = await response.json();
            window.debugLog(`Received ${data.length} genes for condition: ${condition}`, { data });
            if (Array.isArray(data)) {
                allResults.push(...data);
            }
            else {
                window.warnLog('Non-array response for condition', { condition, data });
            }
        }
        window.debugLog(`Total results before deduplication: ${allResults.length}`);
        // Remove duplicates based on gene_symbol
        const uniqueResults = Array.from(new Map(allResults.map(item => {
            const key = item.gene_symbol || item.gene || '';
            return [key, item];
        })).values());
        window.debugLog(`Unique results after deduplication: ${uniqueResults.length}`);
        const duration = performance.now() - startTime;
        window.debugLog(`Query completed in ${duration.toFixed(2)}ms`);
        showResults(uniqueResults, 'Genes Associated with: ' + selected.join(', '));
    }
    catch (error) {
        window.errorLog('Error in queryByCondition', error);
        hideLoading();
        const resultsEl = document.getElementById('results');
        if (resultsEl) {
            resultsEl.innerHTML = '<div class="error">Error: ' + escapeHtml(error.message) + '</div>';
        }
        else {
            window.errorLog('Results element not found for error display');
        }
    }
}
async function queryByTrait() {
    window.debugLog('queryByTrait() called');
    const startTime = performance.now();
    const selected = (window.multiselectState && window.multiselectState.trait) ? window.multiselectState.trait.selected : [];
    window.debugLog('Selected traits', { selected, count: selected.length });
    if (selected.length === 0) {
        window.warnLog('No traits selected');
        alert('Please select at least one trait');
        return;
    }
    showLoading();
    try {
        // Query for each trait and combine results
        const allResults = [];
        for (const trait of selected) {
            window.debugLog(`Querying trait: ${trait}`);
            const url = '/api/genes-by-trait?trait=' + encodeURIComponent(trait);
            window.debugLog('Fetching', { url });
            const response = await fetch(url);
            window.debugLog('Response received', {
                trait,
                status: response.status,
                ok: response.ok
            });
            if (!response.ok) {
                throw new Error(`HTTP ${response.status} for trait: ${trait}`);
            }
            const data = await response.json();
            window.debugLog(`Received ${data.length} genes for trait: ${trait}`, { data });
            if (Array.isArray(data)) {
                allResults.push(...data);
            }
            else {
                window.warnLog('Non-array response for trait', { trait, data });
            }
        }
        window.debugLog(`Total results before deduplication: ${allResults.length}`);
        // Remove duplicates
        const uniqueResults = Array.from(new Map(allResults.map(item => {
            const key = item.gene_symbol || item.gene || '';
            return [key, item];
        })).values());
        window.debugLog(`Unique results after deduplication: ${uniqueResults.length}`);
        const duration = performance.now() - startTime;
        window.debugLog(`Query completed in ${duration.toFixed(2)}ms`);
        showResults(uniqueResults, 'Genes Associated with Trait(s): ' + selected.join(', '));
    }
    catch (error) {
        window.errorLog('Error in queryByTrait', error);
        hideLoading();
        const resultsEl = document.getElementById('results');
        if (resultsEl) {
            resultsEl.innerHTML = '<div class="error">Error: ' + escapeHtml(error.message) + '</div>';
        }
        else {
            window.errorLog('Results element not found for error display');
        }
    }
}
async function queryByGene() {
    window.debugLog('queryByGene() called');
    const startTime = performance.now();
    const selected = (window.multiselectState && window.multiselectState.gene) ? window.multiselectState.gene.selected : [];
    window.debugLog('Selected genes', { selected, count: selected.length });
    if (selected.length === 0) {
        window.warnLog('No genes selected');
        alert('Please select at least one gene');
        return;
    }
    showLoading();
    try {
        // Query for each gene
        const allResults = [];
        for (const gene of selected) {
            window.debugLog(`Querying gene: ${gene}`);
            const url = '/api/gene-info?gene=' + encodeURIComponent(gene);
            window.debugLog('Fetching', { url });
            const response = await fetch(url);
            window.debugLog('Response received', {
                gene,
                status: response.status,
                ok: response.ok
            });
            if (!response.ok) {
                throw new Error(`HTTP ${response.status} for gene: ${gene}`);
            }
            const data = await response.json();
            window.debugLog(`Received data for gene: ${gene}`, { data });
            if ('error' in data) {
                window.warnLog('Error in gene data', { gene, error: data.error });
            }
            allResults.push(data);
        }
        const duration = performance.now() - startTime;
        window.debugLog(`Query completed in ${duration.toFixed(2)}ms`);
        showResults(allResults, 'Gene Information: ' + selected.join(', '));
    }
    catch (error) {
        window.errorLog('Error in queryByGene', error);
        hideLoading();
        const resultsEl = document.getElementById('results');
        if (resultsEl) {
            resultsEl.innerHTML = '<div class="error">Error: ' + escapeHtml(error.message) + '</div>';
        }
        else {
            window.errorLog('Results element not found for error display');
        }
    }
}
async function queryAllGenes() {
    showLoading();
    try {
        const response = await fetch('/api/all-genes');
        const data = await response.json();
        showResults(data, 'All Genes in Database');
    }
    catch (error) {
        hideLoading();
        const resultsEl = document.getElementById('results');
        if (resultsEl) {
            resultsEl.innerHTML = '<div class="error">Error: ' + escapeHtml(error.message) + '</div>';
        }
    }
}
async function queryPharmacogenomic() {
    showLoading();
    try {
        const response = await fetch('/api/pharmacogenomic');
        const data = await response.json();
        showResults(data, 'Pharmacogenomic Medication Metabolism Data');
    }
    catch (error) {
        hideLoading();
        const resultsEl = document.getElementById('results');
        if (resultsEl) {
            resultsEl.innerHTML = '<div class="error">Error: ' + escapeHtml(error.message) + '</div>';
        }
    }
}
// Make functions globally available
window.queryByCondition = queryByCondition;
window.queryByTrait = queryByTrait;
window.queryByGene = queryByGene;
window.queryAllGenes = queryAllGenes;
window.queryPharmacogenomic = queryPharmacogenomic;
