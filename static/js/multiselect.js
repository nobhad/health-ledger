"use strict";
/**
 * Multiselect component for query interface
 * Handles dropdown selection with filtering and tag display
 */
// Ensure debug functions are available
if (typeof window.debugLog === 'undefined') {
    window.debugLog = function (message, ...args) {
        console.log(`[MULTISELECT DEBUG] ${message}`, ...args);
    };
}
if (typeof window.errorLog === 'undefined') {
    window.errorLog = function (message, error, ...args) {
        console.error(`[MULTISELECT ERROR] ${message}`, error, ...args);
        if (error && error.stack) {
            console.error('Stack trace:', error.stack);
        }
    };
}
if (typeof window.warnLog === 'undefined') {
    window.warnLog = function (message, ...args) {
        console.warn(`[MULTISELECT WARN] ${message}`, ...args);
    };
}
// Multiselect state - must be on window for query.ts to access it
// IMPORTANT: Use singular keys ('condition', 'trait', 'gene') to match type parameter
if (!window.multiselectState) {
    window.multiselectState = {
        condition: { options: [], selected: [] },
        trait: { options: [], selected: [] },
        gene: { options: [], selected: [] }
    };
}
window.debugLog('Multiselect state initialized', window.multiselectState);
function initMultiselect(type, inputId, dropdownId, tagsId) {
    window.debugLog(`initMultiselect() called`, { type, inputId, dropdownId, tagsId });
    const input = document.getElementById(inputId);
    const dropdown = document.getElementById(dropdownId);
    const tags = document.getElementById(tagsId);
    window.debugLog('Elements found', {
        input: !!input,
        dropdown: !!dropdown,
        tags: !!tags
    });
    if (!input || !dropdown || !tags) {
        window.errorLog('Multiselect elements not found for type', null, {
            type,
            inputId,
            dropdownId,
            tagsId,
            inputFound: !!input,
            dropdownFound: !!dropdown,
            tagsFound: !!tags
        });
        return;
    }
    // Ensure state is initialized (use window.multiselectState)
    // CRITICAL: Don't overwrite existing state if it has data!
    // IMPORTANT: Use singular keys to match type parameter
    if (!window.multiselectState) {
        window.multiselectState = {
            condition: { options: [], selected: [] },
            trait: { options: [], selected: [] },
            gene: { options: [], selected: [] }
        };
    }
    // Only initialize if it doesn't exist - don't overwrite if it has options!
    if (!window.multiselectState[type]) {
        window.debugLog(`Initializing state for type: ${type}`);
        window.multiselectState[type] = { options: [], selected: [] };
    }
    else {
        // State exists - ensure selected array exists but don't overwrite options
        if (!window.multiselectState[type].selected) {
            window.debugLog(`Initializing selected array for type: ${type}`);
            window.multiselectState[type].selected = [];
        }
        // Ensure options is an array (don't overwrite if it has data)
        if (!Array.isArray(window.multiselectState[type].options)) {
            window.debugLog(`Fixing options array for type: ${type} - was not an array`);
            window.multiselectState[type].options = [];
        }
    }
    window.debugLog(`State for ${type}`, {
        optionsCount: window.multiselectState[type].options?.length || 0,
        optionsIsArray: Array.isArray(window.multiselectState[type].options),
        selectedCount: window.multiselectState[type].selected?.length || 0
    });
    // Show dropdown on focus - always update and show if there are options
    input.addEventListener('focus', () => {
        window.debugLog(`Input focused for ${type}`);
        // Always read fresh state from window - don't use cached references
        const state = window.multiselectState?.[type];
        const hasOptions = state && Array.isArray(state.options) && state.options.length > 0;
        window.debugLog(`Focus handler state check for ${type}`, {
            stateExists: !!state,
            hasOptions: hasOptions,
            optionsCount: state?.options?.length || 0,
            optionsIsArray: Array.isArray(state?.options)
        });
        // Always update dropdown - it will handle empty state gracefully
        updateMultiselectDropdown(type, input.value);
        // Show dropdown if there are options
        if (hasOptions) {
            dropdown.style.display = 'block';
            dropdown.classList.add('show');
            window.debugLog(`Dropdown shown for ${type} with ${state.options.length} options`);
        }
        else {
            // Still show dropdown but with loading/empty message
            dropdown.style.display = 'block';
            dropdown.classList.add('show');
            window.debugLog(`Dropdown shown for ${type} but no options available yet`);
        }
    });
    // Filter on input (only show if there are options)
    input.addEventListener('input', (e) => {
        const target = e.target;
        window.debugLog(`Input changed for ${type}`, { value: target.value });
        const state = (window.multiselectState && window.multiselectState[type]) ? window.multiselectState[type] : null;
        updateMultiselectDropdown(type, target.value);
        if (state && state.options && Array.isArray(state.options) && state.options.length > 0) {
            dropdown.style.display = 'block';
            dropdown.classList.add('show');
        }
    });
    // Click on input to show dropdown (only if there are options)
    input.addEventListener('click', (e) => {
        window.debugLog(`Input clicked for ${type}`);
        e.stopPropagation();
        const state = (window.multiselectState && window.multiselectState[type]) ? window.multiselectState[type] : null;
        updateMultiselectDropdown(type, input.value);
        if (state && state.options && Array.isArray(state.options) && state.options.length > 0) {
            dropdown.style.display = 'block';
            dropdown.classList.add('show');
        }
        else {
            window.debugLog(`Dropdown not shown - no options available yet for ${type}`);
            dropdown.style.display = 'none';
        }
    });
    // Also show on any interaction (only if there are options)
    input.addEventListener('keydown', (e) => {
        if (e.key !== 'Escape') {
            const state = (window.multiselectState && window.multiselectState[type]) ? window.multiselectState[type] : null;
            updateMultiselectDropdown(type, input.value);
            if (state && state.options && Array.isArray(state.options) && state.options.length > 0) {
                dropdown.style.display = 'block';
                dropdown.classList.add('show');
            }
        }
    });
    // Hide dropdown on blur (with delay to allow clicks)
    input.addEventListener('blur', () => {
        setTimeout(() => {
            dropdown.classList.remove('show');
            dropdown.style.display = 'none';
        }, 200);
    });
    // Keep dropdown open when clicking inside it
    dropdown.addEventListener('mousedown', (e) => {
        e.preventDefault();
    });
    // Update tags display (only if state exists)
    if (window.multiselectState && window.multiselectState[type] && window.multiselectState[type].selected) {
        updateMultiselectTags(type);
    }
}
function updateMultiselectDropdown(type, filter = '') {
    window.debugLog(`updateMultiselectDropdown() called`, { type, filter });
    // Use window.multiselectState to ensure we get the shared state
    const state = (window.multiselectState && window.multiselectState[type]) ? window.multiselectState[type] : null;
    const dropdown = document.getElementById(type + 'Dropdown');
    window.debugLog('State and dropdown', {
        stateExists: !!state,
        stateOptionsCount: state?.options?.length || 0,
        dropdownExists: !!dropdown,
        windowStateExists: !!window.multiselectState,
        windowStateType: window.multiselectState ? (window.multiselectState[type] ? 'exists' : 'missing') : 'no state',
        windowStateOptionsCount: window.multiselectState && window.multiselectState[type] ? window.multiselectState[type].options?.length || 0 : 0
    });
    if (!dropdown) {
        window.errorLog('Dropdown not found for type', null, { type, dropdownId: type + 'Dropdown' });
        return;
    }
    // ALWAYS use window.multiselectState directly - it's the source of truth
    // Get the state object directly - don't use intermediate variables
    if (!window.multiselectState || !window.multiselectState[type]) {
        window.debugLog(`No state found for ${type}`, {
            windowStateExists: !!window.multiselectState,
            typeStateExists: !!(window.multiselectState && window.multiselectState[type])
        });
        if (dropdown.classList.contains('show') || dropdown.style.display === 'block') {
            dropdown.innerHTML = '<div class="multiselect-option multiselect-option--empty">Loading options...</div>';
        }
        return;
    }
    const stateToUse = window.multiselectState[type];
    window.debugLog('Final state check', {
        windowStateExists: !!window.multiselectState,
        typeStateExists: !!(window.multiselectState && window.multiselectState[type]),
        stateToUseExists: !!stateToUse,
        stateToUseOptionsCount: stateToUse?.options?.length || 0,
        stateToUseOptionsType: stateToUse?.options ? typeof stateToUse.options : 'no options property',
        stateToUseIsArray: stateToUse?.options ? Array.isArray(stateToUse.options) : false,
        directCheck: window.multiselectState[type]?.options?.length || 0,
        directIsArray: Array.isArray(window.multiselectState[type]?.options)
    });
    // Double-check directly from window - sometimes stateToUse is a stale reference
    // CRITICAL: Always read fresh from window.multiselectState - don't use cached references
    const directOptions = window.multiselectState?.[type]?.options;
    const hasOptions = Array.isArray(directOptions) && directOptions.length > 0;
    window.debugLog(`Options check for ${type}`, {
        directOptionsExists: !!directOptions,
        directOptionsIsArray: Array.isArray(directOptions),
        directOptionsLength: directOptions?.length || 0,
        hasOptions: hasOptions,
        windowStateType: typeof window.multiselectState,
        windowStateHasType: !!(window.multiselectState && window.multiselectState[type]),
        typeStateKeys: window.multiselectState?.[type] ? Object.keys(window.multiselectState[type]) : 'no type state',
        fullState: window.multiselectState ? JSON.stringify(Object.keys(window.multiselectState)) : 'no state'
    });
    if (!hasOptions) {
        window.debugLog(`No options available for ${type}`, {
            stateToUseExists: !!stateToUse,
            stateToUseOptions: stateToUse?.options?.length || 0,
            directOptionsCount: directOptions?.length || 0,
            directIsArray: Array.isArray(directOptions),
            windowStateKeys: window.multiselectState ? Object.keys(window.multiselectState) : 'no state',
            typeStateKeys: window.multiselectState?.[type] ? Object.keys(window.multiselectState[type]) : 'no type state',
            fullStateSnapshot: window.multiselectState ? JSON.parse(JSON.stringify(window.multiselectState)) : null
        });
        // Only show loading if dropdown is visible (focused) - don't auto-show
        if (dropdown.classList.contains('show') || dropdown.style.display === 'block') {
            dropdown.innerHTML = '<div class="multiselect-option multiselect-option--empty">Loading options... (If this persists, check console for errors)</div>';
        }
        else {
            // Clear loading message if dropdown is hidden
            dropdown.innerHTML = '';
        }
        return;
    }
    // Use direct options from window - guaranteed fresh
    // CRITICAL: Re-read from window to ensure we have the latest state
    // Read multiple times to ensure we get the latest
    const freshState = window.multiselectState?.[type];
    const optionsToUse = freshState?.options || [];
    window.debugLog(`Updating dropdown with ${optionsToUse.length} options, filter: "${filter}"`, {
        optionsLength: optionsToUse.length,
        optionsIsArray: Array.isArray(optionsToUse),
        firstOption: optionsToUse.length > 0 ? optionsToUse[0] : 'none',
        freshStateExists: !!freshState,
        freshStateKeys: freshState ? Object.keys(freshState) : []
    });
    if (!Array.isArray(optionsToUse) || optionsToUse.length === 0) {
        window.debugLog(`No options to display for ${type}`, {
            optionsType: typeof optionsToUse,
            optionsIsArray: Array.isArray(optionsToUse),
            optionsLength: optionsToUse?.length || 0,
            freshStateExists: !!freshState,
            freshStateOptions: freshState?.options ? (Array.isArray(freshState.options) ? freshState.options.length : 'not array') : 'no options property'
        });
        // Only show message if dropdown is visible
        if (dropdown.classList.contains('show') || dropdown.style.display === 'block') {
            dropdown.innerHTML = '<div class="multiselect-option multiselect-option--empty">No options available. Data may still be loading...</div>';
        }
        else {
            dropdown.innerHTML = '';
        }
        return;
    }
    const filterLower = filter.toLowerCase();
    dropdown.innerHTML = '';
    let hasResults = false;
    let shownCount = 0;
    const maxShow = 50; // Limit to 50 options for performance
    // Get selected from state - re-read fresh
    const selectedValues = window.multiselectState[type]?.selected || [];
    optionsToUse.forEach(option => {
        if (filter && !option.label.toLowerCase().includes(filterLower)) {
            return;
        }
        if (shownCount >= maxShow) {
            return;
        }
        hasResults = true;
        shownCount++;
        const isSelected = Array.isArray(selectedValues) && selectedValues.includes(option.value);
        const optionDiv = document.createElement('div');
        optionDiv.className = 'multiselect-option' + (isSelected ? ' selected' : '');
        optionDiv.style.cursor = 'pointer';
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.checked = isSelected;
        checkbox.style.cursor = 'pointer';
        checkbox.onchange = () => toggleMultiselectOption(type, option.value);
        optionDiv.appendChild(checkbox);
        // Add icon based on type
        const iconSpan = document.createElement('span');
        iconSpan.className = 'multiselect-option-icon';
        let iconName = 'circle';
        if (type === 'condition') {
            iconName = 'heart-pulse';
        }
        else if (type === 'trait') {
            iconName = 'user';
        }
        else if (type === 'gene') {
            iconName = 'dna';
        }
        const icon = document.createElement('i');
        icon.setAttribute('data-lucide', iconName);
        iconSpan.appendChild(icon);
        optionDiv.appendChild(iconSpan);
        const label = document.createTextNode(option.label);
        optionDiv.appendChild(label);
        // Initialize Lucide icon after adding to DOM
        if (typeof window.lucide !== 'undefined') {
            window.lucide.createIcons();
        }
        optionDiv.onclick = (e) => {
            e.stopPropagation();
            if (e.target !== checkbox && e.target !== label) {
                checkbox.checked = !checkbox.checked;
                toggleMultiselectOption(type, option.value);
            }
        };
        dropdown.appendChild(optionDiv);
    });
    if (!hasResults) {
        dropdown.innerHTML = '<div class="multiselect-option multiselect-option--empty">No results found. Try a different search term.</div>';
    }
    else if (shownCount >= maxShow) {
        const moreDiv = document.createElement('div');
        moreDiv.className = 'multiselect-option';
        moreDiv.style.padding = '10px';
        moreDiv.style.textAlign = 'center';
        moreDiv.style.color = '#666';
        moreDiv.style.fontStyle = 'italic';
        moreDiv.textContent = `... and ${optionsToUse.length - shownCount} more. Type to filter.`;
        dropdown.appendChild(moreDiv);
    }
    // Only show dropdown if it was already visible (user is interacting)
    // Don't auto-show on data load - wait for user to click/focus
    if (dropdown.classList.contains('show') || dropdown.style.display === 'block') {
        dropdown.style.display = 'block';
        dropdown.style.visibility = 'visible';
        dropdown.style.opacity = '1';
    }
    // Initialize Lucide icons for all options
    if (typeof window.lucide !== 'undefined') {
        window.lucide.createIcons();
    }
    window.debugLog(`Dropdown updated for ${type}`, {
        optionsShown: shownCount,
        totalOptions: optionsToUse.length,
        dropdownVisible: dropdown.style.display === 'block' || dropdown.classList.contains('show')
    });
}
function toggleMultiselectOption(type, value) {
    window.debugLog(`toggleMultiselectOption() called`, { type, value });
    // Always use window.multiselectState directly
    if (!window.multiselectState || !window.multiselectState[type]) {
        window.warnLog('State not found', { type, stateExists: !!window.multiselectState });
        return;
    }
    const state = window.multiselectState[type];
    if (!state.selected) {
        state.selected = [];
    }
    const index = state.selected.indexOf(value);
    const wasSelected = index > -1;
    if (wasSelected) {
        window.debugLog(`Removing ${value} from ${type} selection`);
        state.selected.splice(index, 1);
    }
    else {
        window.debugLog(`Adding ${value} to ${type} selection`);
        state.selected.push(value);
    }
    window.debugLog(`Updated selection for ${type}`, { selected: state.selected });
    updateMultiselectTags(type);
    const input = document.getElementById(type + 'Input');
    if (input) {
        updateMultiselectDropdown(type, input.value);
    }
    else {
        window.warnLog('Input element not found', { type, inputId: type + 'Input' });
    }
}
function updateMultiselectTags(type) {
    // Always use window.multiselectState directly
    if (!window.multiselectState || !window.multiselectState[type]) {
        return;
    }
    const state = window.multiselectState[type];
    const tags = document.getElementById(type + 'Tags');
    if (!state.selected || !tags) {
        return;
    }
    tags.innerHTML = '';
    if (!Array.isArray(state.selected) || state.selected.length === 0) {
        return;
    }
    state.selected.forEach((value) => {
        const option = (state.options && Array.isArray(state.options)) ? state.options.find((opt) => opt.value === value) : null;
        if (!option) {
            return;
        }
        // Built with DOM APIs rather than an inline onclick string: a value
        // containing an apostrophe (e.g. "Alzheimer's disease") used to produce
        // a JavaScript syntax error and the tag could not be removed.
        const tag = document.createElement('div');
        tag.className = 'multiselect-tag';
        const labelSpan = document.createElement('span');
        labelSpan.textContent = option.label;
        const removeSpan = document.createElement('span');
        removeSpan.className = 'multiselect-tag-remove';
        removeSpan.textContent = '×';
        removeSpan.addEventListener('click', () => removeMultiselectOption(type, value));
        tag.appendChild(labelSpan);
        tag.appendChild(removeSpan);
        tags.appendChild(tag);
    });
}
function removeMultiselectOption(type, value) {
    // Always use window.multiselectState directly
    if (!window.multiselectState || !window.multiselectState[type]) {
        return;
    }
    const state = window.multiselectState[type];
    if (!state.selected || !Array.isArray(state.selected)) {
        return;
    }
    const index = state.selected.indexOf(value);
    if (index > -1) {
        state.selected.splice(index, 1);
        updateMultiselectTags(type);
        const input = document.getElementById(type + 'Input');
        if (input) {
            updateMultiselectDropdown(type, input.value);
        }
    }
}
// Make functions globally available
window.initMultiselect = initMultiselect;
window.updateMultiselectDropdown = updateMultiselectDropdown;
window.toggleMultiselectOption = toggleMultiselectOption;
window.removeMultiselectOption = removeMultiselectOption;
