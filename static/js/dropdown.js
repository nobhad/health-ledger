"use strict";
/**
 * Dropdown — the portal's PortalDropdown shape for a native <select>.
 *
 * A native select's popup is drawn by the OS and cannot take the design
 * system, so each select.form-select / select.filter-select is wrapped in a
 * trigger button and a listbox menu (styles in components.css). The select
 * stays in the DOM, hidden: forms still submit it and scripts still read
 * its value and hear its change event.
 */
(function () {
    const CARET = '<svg class="dropdown-caret" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" ' +
        'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
        '<path d="m6 9 6 6 6-6"/></svg>';
    function enhance(select) {
        if (select.dataset.enhanced === 'true' || !select.parentNode) {
            return;
        }
        select.dataset.enhanced = 'true';
        const wrapper = document.createElement('div');
        wrapper.className = 'dropdown';
        select.parentNode.insertBefore(wrapper, select);
        wrapper.appendChild(select);
        select.classList.add('dropdown-native');
        select.tabIndex = -1;
        select.setAttribute('aria-hidden', 'true');
        const baseId = select.id || `dropdown-${Math.random().toString(36).slice(2, 8)}`;
        const trigger = document.createElement('button');
        trigger.type = 'button';
        trigger.className = 'dropdown-trigger';
        trigger.id = `${baseId}Trigger`;
        trigger.setAttribute('aria-haspopup', 'listbox');
        trigger.setAttribute('aria-expanded', 'false');
        trigger.setAttribute('aria-controls', `${baseId}Menu`);
        trigger.dataset.state = 'closed';
        const value = document.createElement('span');
        value.className = 'dropdown-value';
        trigger.appendChild(value);
        trigger.insertAdjacentHTML('beforeend', CARET);
        const menu = document.createElement('ul');
        menu.className = 'dropdown-menu';
        menu.id = `${baseId}Menu`;
        menu.setAttribute('role', 'listbox');
        menu.hidden = true;
        const items = Array.from(select.options).map((option, index) => {
            const item = document.createElement('li');
            item.className = 'dropdown-item';
            item.setAttribute('role', 'option');
            item.tabIndex = -1;
            item.textContent = option.text.trim();
            item.addEventListener('click', () => choose(index));
            menu.appendChild(item);
            return item;
        });
        wrapper.appendChild(trigger);
        wrapper.appendChild(menu);
        // The label keeps pointing at something focusable.
        if (select.id) {
            const label = document.querySelector(`label[for="${select.id}"]`);
            if (label) {
                label.htmlFor = trigger.id;
                trigger.setAttribute('aria-labelledby', label.id || (label.id = `${baseId}Label`));
            }
        }
        function sync() {
            const current = select.selectedIndex;
            value.textContent = current >= 0 ? select.options[current].text.trim() : '';
            items.forEach((item, index) => item.setAttribute('aria-selected', String(index === current)));
        }
        function open() {
            menu.hidden = false;
            trigger.setAttribute('aria-expanded', 'true');
            trigger.dataset.state = 'open';
            const focusIndex = Math.max(select.selectedIndex, 0);
            if (items[focusIndex]) {
                items[focusIndex].focus();
            }
        }
        function close(focusTrigger = false) {
            if (menu.hidden) {
                return;
            }
            menu.hidden = true;
            trigger.setAttribute('aria-expanded', 'false');
            trigger.dataset.state = 'closed';
            if (focusTrigger) {
                trigger.focus();
            }
        }
        function choose(index) {
            if (select.selectedIndex !== index) {
                select.selectedIndex = index;
                select.dispatchEvent(new Event('change', { bubbles: true }));
            }
            sync();
            close(true);
        }
        trigger.addEventListener('click', () => (menu.hidden ? open() : close()));
        trigger.addEventListener('keydown', (event) => {
            if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
                event.preventDefault();
                open();
            }
        });
        menu.addEventListener('keydown', (event) => {
            const current = items.indexOf(document.activeElement);
            switch (event.key) {
                case 'ArrowDown':
                    event.preventDefault();
                    items[Math.min(current + 1, items.length - 1)].focus();
                    break;
                case 'ArrowUp':
                    event.preventDefault();
                    items[Math.max(current - 1, 0)].focus();
                    break;
                case 'Home':
                    event.preventDefault();
                    items[0].focus();
                    break;
                case 'End':
                    event.preventDefault();
                    items[items.length - 1].focus();
                    break;
                case 'Enter':
                case ' ':
                    event.preventDefault();
                    if (current >= 0) {
                        choose(current);
                    }
                    break;
                case 'Escape':
                    event.preventDefault();
                    close(true);
                    break;
                case 'Tab':
                    close();
                    break;
                default:
                    break;
            }
        });
        document.addEventListener('click', (event) => {
            if (!wrapper.contains(event.target)) {
                close();
            }
        });
        select.addEventListener('change', sync);
        sync();
    }
    document
        .querySelectorAll('select.form-select, select.filter-select')
        .forEach(enhance);
})();
