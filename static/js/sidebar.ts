/**
 * Sidebar: collapse on desktop, drawer on phones.
 *
 * State lives on <html data-sidebar="open|collapsed">, set before first paint
 * by the inline script in base.html and persisted under
 * "health-ledger-sidebar". The phone drawer is a separate, transient state:
 * .is-open on the sidebar plus a backdrop.
 */
(function (): void {
    const STORAGE_KEY = 'health-ledger-sidebar';
    /* --mobile in static/css/design-system/tokens/breakpoints.css (max-width: 767px). */
    const PHONE_MAX_WIDTH_PX = 767;

    const root = document.documentElement;
    const sidebar = document.getElementById('sidebar');
    const collapse = document.getElementById('sidebarCollapse');
    const toggle = document.getElementById('sidebarToggle');
    const backdrop = document.getElementById('sidebarBackdrop');
    if (!sidebar || !collapse || !toggle || !backdrop) {
        return;
    }

    function isCollapsed(): boolean {
        return root.getAttribute('data-sidebar') === 'collapsed';
    }

    function applyCollapseLabel(): void {
        const collapsed = isCollapsed();
        collapse!.setAttribute('aria-expanded', String(!collapsed));
        collapse!.setAttribute('aria-label', collapsed ? 'Expand sidebar' : 'Collapse sidebar');
        collapse!.setAttribute('title', collapsed ? 'Expand' : 'Collapse');
    }

    collapse.addEventListener('click', () => {
        const next = isCollapsed() ? 'open' : 'collapsed';
        root.setAttribute('data-sidebar', next);
        try {
            localStorage.setItem(STORAGE_KEY, next);
        } catch (e) {
            /* storage unavailable; the choice lasts for this page only */
        }
        applyCollapseLabel();
    });

    function setDrawer(open: boolean): void {
        sidebar!.classList.toggle('is-open', open);
        toggle!.setAttribute('aria-expanded', String(open));
        backdrop!.hidden = !open;
    }

    toggle.addEventListener('click', () => setDrawer(!sidebar.classList.contains('is-open')));
    backdrop.addEventListener('click', () => setDrawer(false));
    sidebar.addEventListener('click', (event) => {
        if ((event.target as HTMLElement).closest('a')) {
            setDrawer(false);
        }
    });
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            setDrawer(false);
        }
    });

    const phone = window.matchMedia(`(max-width: ${PHONE_MAX_WIDTH_PX}px)`);
    phone.addEventListener('change', () => {
        if (!phone.matches) {
            setDrawer(false);
        }
    });

    applyCollapseLabel();
})();
