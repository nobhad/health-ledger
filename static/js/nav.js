"use strict";
/**
 * Hamburger navigation.
 *
 * Below the desktop breakpoint the nav is a drawer under the header
 * (layout.css, @media (--tablet-down)); this wires the toggle, closes the
 * drawer on Escape, on a link, and when the window grows past the
 * breakpoint.
 */
(function () {
    /* One past --wide-down (max-width: 1300px) in
       static/css/design-system/tokens/breakpoints.css, the drawer's breakpoint. */
    const DESKTOP_MIN_WIDTH_PX = 1301;
    const toggle = document.getElementById('navToggle');
    const nav = document.getElementById('mainNav');
    if (!toggle || !nav) {
        return;
    }
    function setOpen(open) {
        nav.classList.toggle('is-open', open);
        toggle.setAttribute('aria-expanded', String(open));
    }
    toggle.addEventListener('click', () => setOpen(!nav.classList.contains('is-open')));
    nav.addEventListener('click', (event) => {
        if (event.target.closest('a')) {
            setOpen(false);
        }
    });
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            setOpen(false);
        }
    });
    const desktop = window.matchMedia(`(min-width: ${DESKTOP_MIN_WIDTH_PX}px)`);
    desktop.addEventListener('change', () => {
        if (desktop.matches) {
            setOpen(false);
        }
    });
})();
