"use strict";
// Primary Sources Viewer - Multi-Panel Interface
/**
 * Format a date from the API for display.
 *
 * Dates arrive as "YYYY-MM-DD". `new Date("2019-11-18")` parses that as UTC
 * midnight, so toLocaleDateString() showed the previous day anywhere west of
 * Greenwich. Build the date from its parts so it is interpreted as local time.
 */
function formatDate(value, fallback) {
    if (!value) {
        return fallback;
    }
    const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(value);
    const date = match
        ? new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]))
        : new Date(value);
    return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString();
}
// Load sources on page load
document.addEventListener('DOMContentLoaded', function () {
    loadSources();
    setupFilters();
    setupPanelResizing();
});
function setupFilters() {
    const searchInput = document.getElementById('searchInput');
    const typeFilter = document.getElementById('typeFilter');
    const startDate = document.getElementById('startDate');
    const endDate = document.getElementById('endDate');
    const debouncedLoadSources = debounce(loadSources, 300);
    searchInput.addEventListener('input', () => debouncedLoadSources());
    typeFilter.addEventListener('change', loadSources);
    startDate.addEventListener('change', loadSources);
    endDate.addEventListener('change', loadSources);
}
function loadSources() {
    const searchInput = document.getElementById('searchInput');
    const typeFilter = document.getElementById('typeFilter');
    const startDate = document.getElementById('startDate');
    const endDate = document.getElementById('endDate');
    const params = new URLSearchParams();
    if (searchInput.value) {
        params.append('search', searchInput.value);
    }
    if (typeFilter.value) {
        params.append('type', typeFilter.value);
    }
    if (startDate.value) {
        params.append('start_date', startDate.value);
    }
    if (endDate.value) {
        params.append('end_date', endDate.value);
    }
    fetch(`/api/sources?${params.toString()}`)
        .then(response => response.json())
        .then(data => {
        if (data.success) {
            displaySourcesList(data.sources);
        }
        else {
            console.error('Error loading sources:', data.message);
        }
    })
        .catch(error => {
        console.error('Error loading sources:', error);
    });
}
function displaySourcesList(sources) {
    const list = document.getElementById('sourcesList');
    if (!list) {
        return;
    }
    if (sources.length === 0) {
        // An empty list means two different things, and saying the wrong one
        // sends somebody looking for a filter they never set.
        const filtered = ['searchInput', 'typeFilter', 'startDate', 'endDate']
            .some(id => document.getElementById(id)?.value);
        list.innerHTML = filtered
            ? '<li class="sources-list-item is-empty">Nothing matches what you are looking for.</li>'
            : '<li class="is-empty"><div class="empty-state">'
                + '<p>No records yet. Lab results, visit notes, letters and DNA files '
                + 'you add are listed here.</p>'
                + '<a class="btn btn-primary" href="/import">Add your first record</a>'
                + '</div></li>';
        return;
    }
    list.innerHTML = sources.map(source => {
        const date = formatDate(source.document_date, 'No date');
        return `
            <li class="sources-list-item" data-source-id="${source.id}">
                <div style="font-weight: 500;">${escapeHtmlSource(source.source_name)}</div>
                <div style="font-size: 0.85em; color: #666; margin-top: 4px;">
                    ${escapeHtmlSource(source.source_type)} | ${date}
                </div>
            </li>
        `;
    }).join('');
    // Add click handlers
    list.querySelectorAll('.sources-list-item').forEach((item) => {
        item.addEventListener('click', function () {
            const sourceId = parseInt(this.dataset.sourceId || '0');
            selectSource(sourceId);
        });
    });
}
function selectSource(sourceId) {
    // Update active state
    document.querySelectorAll('.sources-list-item').forEach(item => {
        item.classList.remove('active');
        if (parseInt(item.dataset.sourceId || '0') === sourceId) {
            item.classList.add('active');
        }
    });
    // Load source details
    loadSourceDetails(sourceId);
    loadSourceFindings(sourceId);
}
function loadSourceDetails(sourceId) {
    fetch(`/api/sources/${sourceId}`)
        .then(response => response.json())
        .then(data => {
        if (data.success) {
            displaySourceDetails(data.source);
        }
        else {
            console.error('Error loading source details:', data.message);
        }
    })
        .catch(error => {
        console.error('Error loading source details:', error);
    });
}
function displaySourceDetails(source) {
    const detailsDiv = document.getElementById('sourceDetails');
    if (!detailsDiv) {
        return;
    }
    const date = formatDate(source.document_date, 'Not specified');
    detailsDiv.innerHTML = `
        <h3>${escapeHtmlSource(source.source_name)}</h3>
        <p><strong>Type:</strong> ${escapeHtmlSource(source.source_type)}</p>
        ${source.institution ? `<p><strong>Institution:</strong> ${escapeHtmlSource(source.institution)}</p>` : ''}
        <p><strong>Date:</strong> ${date}</p>
        ${source.file_name ? `<p><strong>File:</strong> ${escapeHtmlSource(source.file_name)}</p>` : ''}
        <div style="margin-top: 20px;">
            <h4>Extracted Text</h4>
            <div class="source-text">${escapeHtmlSource(source.extracted_text || 'No text extracted')}</div>
        </div>
    `;
}
function loadSourceFindings(sourceId) {
    fetch(`/api/sources/${sourceId}/findings`)
        .then(response => response.json())
        .then(data => {
        if (data.success) {
            displayFindings(data.findings);
        }
        else {
            console.error('Error loading findings:', data.message);
        }
    })
        .catch(error => {
        console.error('Error loading findings:', error);
    });
}
function displayFindings(findings) {
    const findingsPanel = document.getElementById('findingsPanel');
    if (!findingsPanel) {
        return;
    }
    if (findings.length === 0) {
        findingsPanel.innerHTML = '<p>No findings extracted</p>';
        return;
    }
    findingsPanel.innerHTML = `
        <p style="font-size: 0.9em; color: #666; margin-bottom: 12px;">
            ${findings.length} finding(s)
        </p>
        <ul class="findings-list">
            ${findings.map(finding => `
                <li class="finding-item">
                    ${finding.finding_type ? `<div class="finding-type">${escapeHtmlSource(finding.finding_type)}</div>` : ''}
                    <div class="finding-text">${escapeHtmlSource(finding.finding_text)}</div>
                    ${finding.finding_date ? `<div class="finding-date">${formatDate(finding.finding_date, '')}</div>` : ''}
                    ${finding.gene_symbol ? `<div class="finding-date">Related to: ${escapeHtmlSource(finding.gene_symbol)}</div>` : ''}
                </li>
            `).join('')}
        </ul>
    `;
}
function setupPanelResizing() {
    const splitter1 = document.getElementById('splitter1');
    const splitter2 = document.getElementById('splitter2');
    const leftPanel = document.querySelector('.sources-panel-left');
    const middlePanel = document.querySelector('.sources-panel-middle');
    const rightPanel = document.querySelector('.sources-panel-right');
    if (!splitter1 || !splitter2 || !leftPanel || !middlePanel || !rightPanel) {
        return;
    }
    let isResizing1 = false;
    let isResizing2 = false;
    splitter1.addEventListener('mousedown', (e) => {
        isResizing1 = true;
        splitter1.classList.add('active');
        document.body.style.cursor = 'col-resize';
        e.preventDefault();
    });
    splitter2.addEventListener('mousedown', (e) => {
        isResizing2 = true;
        splitter2.classList.add('active');
        document.body.style.cursor = 'col-resize';
        e.preventDefault();
    });
    document.addEventListener('mousemove', (e) => {
        if (isResizing1) {
            const container = document.getElementById('sourcesContainer');
            if (container) {
                const containerRect = container.getBoundingClientRect();
                const newWidth = e.clientX - containerRect.left;
                if (newWidth > 200 && newWidth < 500) {
                    leftPanel.style.width = newWidth + 'px';
                }
            }
        }
        else if (isResizing2) {
            const container = document.getElementById('sourcesContainer');
            if (container) {
                const containerRect = container.getBoundingClientRect();
                const rightStart = containerRect.right - rightPanel.offsetWidth;
                const newWidth = rightStart - e.clientX;
                if (newWidth > 250 && newWidth < 600) {
                    rightPanel.style.width = newWidth + 'px';
                }
            }
        }
    });
    document.addEventListener('mouseup', () => {
        if (isResizing1) {
            isResizing1 = false;
            splitter1.classList.remove('active');
            document.body.style.cursor = '';
            savePanelState();
        }
        if (isResizing2) {
            isResizing2 = false;
            splitter2.classList.remove('active');
            document.body.style.cursor = '';
            savePanelState();
        }
    });
}
function savePanelState() {
    const leftPanel = document.querySelector('.sources-panel-left');
    const rightPanel = document.querySelector('.sources-panel-right');
    if (leftPanel && rightPanel) {
        localStorage.setItem('sourcesPanelLeftWidth', leftPanel.style.width);
        localStorage.setItem('sourcesPanelRightWidth', rightPanel.style.width);
    }
}
function loadPanelState() {
    const leftPanel = document.querySelector('.sources-panel-left');
    const rightPanel = document.querySelector('.sources-panel-right');
    if (leftPanel) {
        const savedWidth = localStorage.getItem('sourcesPanelLeftWidth');
        if (savedWidth) {
            leftPanel.style.width = savedWidth;
        }
    }
    if (rightPanel) {
        const savedWidth = localStorage.getItem('sourcesPanelRightWidth');
        if (savedWidth) {
            rightPanel.style.width = savedWidth;
        }
    }
}
function escapeHtmlSource(text) {
    if (!text) {
        return '';
    }
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
function debounce(func, wait) {
    let timeout;
    return function executedFunction() {
        const later = () => {
            clearTimeout(timeout);
            func();
        };
        clearTimeout(timeout);
        timeout = window.setTimeout(later, wait);
    };
}
// Load saved panel state on page load
window.addEventListener('load', loadPanelState);
