/**
 * Type definitions for Health Ledger application
 */

// Debug configuration
interface DebugConfig {
    enabled: boolean;
    logLevel: 'DEBUG' | 'INFO' | 'WARN' | 'ERROR';
    showTimestamps: boolean;
    showStackTraces: boolean;
}

// Multiselect option
interface MultiselectOption {
    value: string;
    label: string;
}

// Multiselect state for a single type
interface MultiselectTypeState {
    options: MultiselectOption[];
    selected: string[];
}

// Complete multiselect state
// IMPORTANT: Use singular keys to match MultiselectType ('condition', 'trait', 'gene')
interface MultiselectState {
    condition: MultiselectTypeState;
    trait: MultiselectTypeState;
    gene: MultiselectTypeState;
    // Allow dynamic access by type string
    [key: string]: MultiselectTypeState | undefined;
}

// Gene data from API
interface GeneData {
    gene_symbol: string;
    gene_name?: string;
    [key: string]: unknown;
}

// Query result item
interface QueryResultItem {
    [key: string]: unknown;
}

// Window extensions - must be in global scope for module: "None"
interface Window {
    GENETIC_PROFILE_DEBUG: DebugConfig;
    debugLog: (message: string, ...args: unknown[]) => void;
    infoLog: (message: string, ...args: unknown[]) => void;
    warnLog: (message: string, ...args: unknown[]) => void;
    errorLog: (message: string, error?: Error | null, ...args: unknown[]) => void;
    perfLog: (operation: string, startTime: number) => void;
    apiLog: (method: string, url: string, data?: unknown, response?: unknown) => void;
    stateLog: (stateName: string, oldValue: unknown, newValue: unknown) => void;
    elementLog: (elementName: string, action: string, data?: unknown) => void;
    initDebugPanel: () => void;
    multiselectState: MultiselectState;
    allResults: QueryResultItem[];
    filterResults: () => void;
    _originalConsoleError?: typeof console.error;
    _originalConsoleWarn?: typeof console.warn;
    initMultiselect: (type: 'condition' | 'trait' | 'gene', inputId: string, dropdownId: string, tagsId: string) => void;
    updateMultiselectDropdown: (type: 'condition' | 'trait' | 'gene', filter?: string) => void;
    toggleMultiselectOption: (type: 'condition' | 'trait' | 'gene', value: string) => void;
    removeMultiselectOption: (type: 'condition' | 'trait' | 'gene', value: string) => void;
    queryByCondition: () => Promise<void>;
    queryByTrait: () => Promise<void>;
    queryByGene: () => Promise<void>;
    queryAllGenes: () => Promise<void>;
    queryPharmacogenomic: () => Promise<void>;
}

// Lucide icons (if available) - global declaration
declare const lucide: {
    createIcons: () => void;
} | undefined;

// Types are available globally via type declarations above

