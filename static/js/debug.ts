/**
 * Debugging utilities for the Health Ledger application
 * Provides comprehensive logging and error tracking
 */

// Global debug configuration
if (!window.GENETIC_PROFILE_DEBUG) {
    window.GENETIC_PROFILE_DEBUG = {
        enabled: true,
        logLevel: 'DEBUG', // DEBUG, INFO, WARN, ERROR
        showTimestamps: true,
        showStackTraces: true
    };
}

// Log levels
const LOG_LEVELS: Record<string, number> = {
    DEBUG: 0,
    INFO: 1,
    WARN: 2,
    ERROR: 3
};

// Get current log level
function getCurrentLogLevel(): number {
    const level = window.GENETIC_PROFILE_DEBUG.logLevel || 'DEBUG';
    return LOG_LEVELS[level] || LOG_LEVELS.DEBUG;
}

// Format timestamp
function getTimestamp(): string {
    if (!window.GENETIC_PROFILE_DEBUG.showTimestamps) {
        return '';
    }
    return new Date().toISOString() + ' ';
}

// Format log message
function formatMessage(level: string, message: string, ...args: unknown[]): unknown[] {
    const timestamp = getTimestamp();
    const prefix = `[${timestamp}${level}]`;
    return [prefix + ' ' + message, ...args];
}

// Debug logger
window.debugLog = function(message: string, ...args: unknown[]): void {
    if (!window.GENETIC_PROFILE_DEBUG.enabled) {
        return;
    }
    if (getCurrentLogLevel() > LOG_LEVELS.DEBUG) {
        return;
    }
    console.log(...formatMessage('DEBUG', message, ...args));
};

// Info logger
window.infoLog = function(message: string, ...args: unknown[]): void {
    if (!window.GENETIC_PROFILE_DEBUG.enabled) {
        return;
    }
    if (getCurrentLogLevel() > LOG_LEVELS.INFO) {
        return;
    }
    console.info(...formatMessage('INFO', message, ...args));
};

// Warning logger
window.warnLog = function(message: string, ...args: unknown[]): void {
    if (!window.GENETIC_PROFILE_DEBUG.enabled) {
        return;
    }
    if (getCurrentLogLevel() > LOG_LEVELS.WARN) {
        return;
    }
    console.warn(...formatMessage('WARN', message, ...args));
};

// Error logger
window.errorLog = function(message: string, error?: Error | null, ...args: unknown[]): void {
    if (!window.GENETIC_PROFILE_DEBUG.enabled) {
        return;
    }
    console.error(...formatMessage('ERROR', message, ...args));
    
    if (error) {
        console.error('Error details:', error);
        if (window.GENETIC_PROFILE_DEBUG.showStackTraces && error.stack) {
            console.error('Stack trace:', error.stack);
        }
    }
};

// Performance logger
window.perfLog = function(operation: string, startTime: number): void {
    if (!window.GENETIC_PROFILE_DEBUG.enabled) {
        return;
    }
    const duration = performance.now() - startTime;
    const color = duration > 1000 ? 'color: red' : duration > 500 ? 'color: orange' : 'color: green';
    console.log(`%c[PERF] ${operation}: ${duration.toFixed(2)}ms`, color);
};

// API call logger
window.apiLog = function(method: string, url: string, data?: unknown, response?: unknown): void {
    if (!window.GENETIC_PROFILE_DEBUG.enabled) {
        return;
    }
    if (getCurrentLogLevel() > LOG_LEVELS.DEBUG) {
        return;
    }
    
    console.group(`🌐 API ${method.toUpperCase()} ${url}`);
    if (data) {
        console.log('📤 Request:', data);
    }
    if (response) {
        console.log('📥 Response:', response);
    }
    console.groupEnd();
};

// State logger
window.stateLog = function(stateName: string, oldValue: unknown, newValue: unknown): void {
    if (!window.GENETIC_PROFILE_DEBUG.enabled) {
        return;
    }
    if (getCurrentLogLevel() > LOG_LEVELS.DEBUG) {
        return;
    }
    console.log(`🔄 State: ${stateName}`, { from: oldValue, to: newValue });
};

// Element logger
window.elementLog = function(elementName: string, action: string, data?: unknown): void {
    if (!window.GENETIC_PROFILE_DEBUG.enabled) {
        return;
    }
    if (getCurrentLogLevel() > LOG_LEVELS.DEBUG) {
        return;
    }
    console.log(`🧩 ${elementName} - ${action}`, data || '');
};

// Initialize debug panel (optional)
window.initDebugPanel = function(): void {
    if (document.getElementById('debug-panel')) {
        return;
    }
    
    const panel = document.createElement('div');
    panel.id = 'debug-panel';
    panel.style.cssText = `
        position: fixed;
        bottom: 10px;
        right: 10px;
        background: rgba(0,0,0,0.8);
        color: white;
        padding: 10px;
        border-radius: 5px;
        font-family: monospace;
        font-size: 12px;
        z-index: 99999;
        max-width: 300px;
    `;
    
    panel.innerHTML = `
        <div><strong>Debug Panel</strong></div>
        <div>
            <label>
                <input type="checkbox" id="debug-enabled" checked>
                Enable Debug
            </label>
        </div>
        <div>
            <label>
                Log Level:
                <select id="debug-level">
                    <option value="DEBUG">DEBUG</option>
                    <option value="INFO">INFO</option>
                    <option value="WARN">WARN</option>
                    <option value="ERROR">ERROR</option>
                </select>
            </label>
        </div>
        <div>
            <button id="debug-clear">Clear Console</button>
        </div>
    `;
    
    document.body.appendChild(panel);
    
    // Event listeners
    const enabledCheckbox = document.getElementById('debug-enabled') as HTMLInputElement;
    const levelSelect = document.getElementById('debug-level') as HTMLSelectElement;
    const clearButton = document.getElementById('debug-clear');
    
    if (enabledCheckbox) {
        enabledCheckbox.addEventListener('change', (e) => {
            const target = e.target as HTMLInputElement;
            window.GENETIC_PROFILE_DEBUG.enabled = target.checked;
        });
    }
    
    if (levelSelect) {
        levelSelect.addEventListener('change', (e) => {
            const target = e.target as HTMLSelectElement;
            window.GENETIC_PROFILE_DEBUG.logLevel = target.value as 'DEBUG' | 'INFO' | 'WARN' | 'ERROR';
        });
    }
    
    if (clearButton) {
        clearButton.addEventListener('click', () => {
            console.clear();
        });
    }
};

// Auto-initialize if in development
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    // Optionally show debug panel
    // window.initDebugPanel();
}

