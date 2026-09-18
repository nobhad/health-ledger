"use strict";
/**
 * Theme toggle for Health Ledger.
 *
 * The design system keys dark mode off html[data-theme="dark"]. The saved
 * choice is applied by an inline script in base.html before first paint;
 * this file only wires the header button.
 */
(function () {
    const STORAGE_KEY = 'health-ledger-theme';
    const root = document.documentElement;
    const toggle = document.getElementById('themeToggle');
    if (!toggle) {
        return;
    }
    function currentTheme() {
        return root.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
    }
    function applyLabel() {
        const next = currentTheme() === 'dark' ? 'light' : 'dark';
        toggle.setAttribute('aria-label', `Switch to ${next} mode`);
    }
    toggle.addEventListener('click', () => {
        const next = currentTheme() === 'dark' ? 'light' : 'dark';
        root.setAttribute('data-theme', next);
        try {
            localStorage.setItem(STORAGE_KEY, next);
        }
        catch (e) {
            /* storage unavailable; the choice lasts for this page only */
        }
        applyLabel();
    });
    applyLabel();
})();
