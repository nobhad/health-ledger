"use strict";
/**
 * Section navigation for rendered documents (profile, summary).
 *
 * Builds a list of links from the document's h2 headings into #docNavList,
 * shows the nav when there are at least two sections, and marks the section
 * currently in view.
 */
(function () {
    const nav = document.getElementById('docNav');
    const list = document.getElementById('docNavList');
    const body = document.getElementById('docBody');
    if (!nav || !list || !body) {
        return;
    }
    const headings = Array.from(body.querySelectorAll('h2'));
    if (headings.length < 2) {
        return;
    }
    const links = new Map();
    headings.forEach((heading, index) => {
        if (!heading.id) {
            heading.id = `section-${index + 1}`;
        }
        const item = document.createElement('li');
        const link = document.createElement('a');
        link.className = 'doc-nav-link';
        link.href = `#${heading.id}`;
        link.textContent = heading.textContent ?? '';
        item.appendChild(link);
        list.appendChild(item);
        links.set(heading, link);
    });
    nav.hidden = false;
    function setActive(heading) {
        links.forEach((link, target) => {
            link.classList.toggle('is-active', target === heading);
        });
    }
    const observer = new IntersectionObserver((entries) => {
        const visible = entries
            .filter((entry) => entry.isIntersecting)
            .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
        if (visible.length > 0) {
            setActive(visible[0].target);
        }
    }, { rootMargin: '-20% 0px -70% 0px', threshold: 0 });
    headings.forEach((heading) => observer.observe(heading));
    setActive(headings[0]);
})();
