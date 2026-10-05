"use strict";
// References page: look journal articles up, save them, and choose the
// passages of their abstracts that go into a specialist's document.
//
// Everything that comes from the server or the person is put into the page
// with textContent or createElement, never built into an HTML string. The whole
// file is one function because static/js is compiled as global scripts and a
// top-level name here would collide with the other pages' scripts.
(function () {
    const MESSAGE_NO_ANSWER = 'The app did not answer. Is it still running?';
    const MESSAGE_LOOKING_UP = 'Looking up…';
    const MESSAGE_NO_RESULTS = 'No articles found.';
    const MESSAGE_NO_MATCH = 'Nothing matches what you are looking for.';
    const MESSAGE_NOTHING_SAVED = 'Nothing saved yet. Look something up and save the articles worth keeping.';
    const MESSAGE_NO_SELECTION = 'Choose an article from the list.';
    const MESSAGE_NO_EXCERPTS = 'No excerpts yet. Select a passage in the abstract and press Add excerpt.';
    const MESSAGE_NO_ABSTRACT = 'This article has no abstract in the index.';
    const META_SEPARATOR = ' · ';
    const DOI_ADDRESS = 'https://doi.org/';
    const PUBMED_ADDRESS = 'https://pubmed.ncbi.nlm.nih.gov/';
    const ABSTRACT_ID = 'abstractText';
    let found = null;
    let saved = [];
    let specialties = [];
    let current = null;
    let confirmingRemove = false;
    let selectedText = '';
    let addButton = null;
    function byId(id) {
        return document.getElementById(id);
    }
    function make(tag, text, className) {
        const node = document.createElement(tag);
        if (text !== undefined) {
            node.textContent = text;
        }
        if (className) {
            node.className = className;
        }
        return node;
    }
    function button(label, className, onClick) {
        const node = make('button', label, className);
        node.type = 'button';
        node.addEventListener('click', onClick);
        return node;
    }
    function joinParts(parts) {
        return parts
            .filter((part) => part !== null && part !== undefined && part !== '')
            .join(META_SEPARATOR);
    }
    function setStatus(message, isError = false) {
        const status = byId('referencesStatus');
        status.textContent = message;
        status.classList.toggle('is-error', isError);
    }
    /** Ask the app; on any failure show its sentence and answer null. */
    async function call(method, url, body) {
        const options = { method };
        if (method !== 'GET') {
            options.headers = { 'Content-Type': 'application/json' };
            options.body = JSON.stringify(body ?? {});
        }
        let reply;
        try {
            const response = await fetch(url, options);
            reply = await response.json();
        }
        catch (_error) {
            setStatus(MESSAGE_NO_ANSWER, true);
            return null;
        }
        if (!reply.success) {
            setStatus(reply.message || MESSAGE_NO_ANSWER, true);
            return null;
        }
        return reply;
    }
    // ---- left panel ------------------------------------------------------
    function listRow(title, meta, extra, active, open) {
        const row = make('li', undefined, active ? 'sources-list-item active' : 'sources-list-item');
        row.tabIndex = 0;
        row.append(make('div', title, 'list-item-title'));
        if (meta) {
            row.append(make('div', meta, 'list-item-meta'));
        }
        if (extra) {
            row.append(make('div', extra, 'list-item-meta'));
        }
        row.addEventListener('click', open);
        row.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                open();
            }
        });
        return row;
    }
    function messageRow(text) {
        return make('li', text, 'sources-list-item is-empty');
    }
    function openSavedId() {
        return current && current.kind === 'saved' ? current.article.id : null;
    }
    function renderResults() {
        const heading = byId('resultsHeading');
        const list = byId('resultsList');
        heading.hidden = found === null;
        list.hidden = found === null;
        if (found === null) {
            return;
        }
        if (found.length === 0) {
            list.replaceChildren(messageRow(MESSAGE_NO_RESULTS));
            return;
        }
        const openId = openSavedId();
        list.replaceChildren(...found.map(result => {
            const meta = joinParts([
                result.kind,
                result.journal,
                result.year,
                typeof result.cited_by === 'number' ? `cited ${result.cited_by} ${result.cited_by === 1 ? 'time' : 'times'}` : null
            ]);
            const active = result.saved_id !== null
                ? result.saved_id === openId
                : current !== null && current.kind === 'preview' && current.result === result;
            return listRow(result.title, meta, result.saved_id !== null ? 'Saved' : '', active, () => {
                if (result.saved_id !== null) {
                    void openSaved(result.saved_id);
                }
                else {
                    showPreview(result);
                }
            });
        }));
    }
    function excerptCountText(count) {
        if (!count) {
            return '';
        }
        return `${count} ${count === 1 ? 'excerpt' : 'excerpts'}`;
    }
    function renderSaved() {
        const list = byId('savedList');
        if (saved.length === 0) {
            list.replaceChildren(messageRow(MESSAGE_NOTHING_SAVED));
            return;
        }
        const needle = byId('savedFilter').value.trim().toLowerCase();
        const shown = saved.filter(article => !needle
            || [article.title, article.authors, article.journal]
                .some(field => (field || '').toLowerCase().includes(needle)));
        if (shown.length === 0) {
            list.replaceChildren(messageRow(MESSAGE_NO_MATCH));
            return;
        }
        const openId = openSavedId();
        list.replaceChildren(...shown.map(article => listRow(article.title, joinParts([article.journal, article.year, excerptCountText(article.excerpt_count)]), '', article.id === openId, () => { void openSaved(article.id); })));
    }
    async function refreshSaved() {
        const reply = await call('GET', '/api/references');
        if (reply && reply.articles) {
            saved = reply.articles;
            renderSaved();
        }
    }
    async function lookUp() {
        const term = byId('lookupTerm').value.trim();
        if (!term) {
            setStatus('Type a gene, condition or medication first.', true);
            return;
        }
        const lookupBtn = byId('lookupBtn');
        lookupBtn.disabled = true;
        setStatus(MESSAGE_LOOKING_UP);
        const reply = await call('POST', '/api/references/search', { term });
        lookupBtn.disabled = false;
        if (!reply) {
            return;
        }
        found = reply.results || [];
        setStatus('');
        renderResults();
    }
    // ---- middle panel ----------------------------------------------------
    // The same order the article's file uses: a stored web address, then the
    // DOI, then PubMed. A citation from an older import often has only the id.
    function articleAddress(article) {
        const url = article.url || '';
        if (/^https?:\/\//i.test(url)) {
            return url;
        }
        if (article.doi) {
            return DOI_ADDRESS + article.doi;
        }
        if (article.pubmed_id) {
            return `${PUBMED_ADDRESS}${article.pubmed_id}/`;
        }
        return '';
    }
    function articleHead(article) {
        const nodes = [make('h3', article.title)];
        if (article.authors) {
            nodes.push(make('p', article.authors));
        }
        const meta = joinParts([article.journal, article.year]);
        if (meta) {
            nodes.push(make('p', meta));
        }
        const url = articleAddress(article);
        if (url) {
            const link = make('a', url);
            link.href = url;
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            const line = make('p');
            line.append(link);
            nodes.push(line);
        }
        return nodes;
    }
    function abstractParagraphs(text, id) {
        const box = make('div');
        if (id) {
            box.id = id;
        }
        text.split(/\n\s*\n/)
            .map(paragraph => paragraph.trim())
            .filter(paragraph => paragraph !== '')
            .forEach(paragraph => box.append(make('p', paragraph)));
        return box;
    }
    function updateAddButton() {
        const selection = window.getSelection();
        const abstractBox = document.getElementById(ABSTRACT_ID);
        let text = '';
        if (selection && abstractBox && !selection.isCollapsed && selection.rangeCount > 0) {
            const range = selection.getRangeAt(0);
            if (abstractBox.contains(range.startContainer) && abstractBox.contains(range.endContainer)) {
                text = selection.toString().trim();
            }
        }
        selectedText = text;
        if (addButton) {
            addButton.disabled = text === '';
        }
    }
    function removeControls(article) {
        const row = make('div', undefined, 'card-actions');
        if (!confirmingRemove) {
            row.append(button('Remove article', 'btn btn-secondary', () => {
                confirmingRemove = true;
                renderMiddle();
            }));
            return row;
        }
        row.append(make('span', 'Remove this article and its excerpts?'), button('Remove', 'btn btn-secondary', () => { void removeArticle(article.id); }), button('Keep', 'btn btn-secondary', () => {
            confirmingRemove = false;
            renderMiddle();
        }));
        return row;
    }
    function renderMiddle() {
        const view = byId('articleView');
        addButton = null;
        if (current === null) {
            view.replaceChildren(make('p', MESSAGE_NO_SELECTION));
            return;
        }
        if (current.kind === 'preview') {
            const result = current.result;
            const nodes = articleHead(result);
            nodes.push(result.abstract ? abstractParagraphs(result.abstract) : make('p', MESSAGE_NO_ABSTRACT));
            const actions = make('div', undefined, 'card-actions');
            actions.append(button('Save to my ledger', 'btn btn-primary', () => { void saveResult(result); }));
            nodes.push(actions);
            view.replaceChildren(...nodes);
            return;
        }
        const article = current.article;
        const nodes = articleHead(article);
        if (article.abstract) {
            nodes.push(make('p', 'Select a passage in the abstract, then press Add excerpt.', 'note'));
            nodes.push(abstractParagraphs(article.abstract, ABSTRACT_ID));
            const actions = make('div', undefined, 'card-actions');
            addButton = button('Add excerpt', 'btn btn-primary', () => { void addExcerpt(article.id); });
            addButton.disabled = true;
            actions.append(addButton);
            nodes.push(actions);
        }
        else if (article.pubmed_id) {
            nodes.push(make('p', 'The abstract has not been fetched yet. Fetching it sends this article\'s PubMed id to Europe PMC.'));
            const actions = make('div', undefined, 'card-actions');
            actions.append(button('Fetch abstract', 'btn btn-primary', () => { void fetchAbstract(article.id); }));
            nodes.push(actions);
        }
        else {
            nodes.push(make('p', 'This article has no PubMed id, so its abstract cannot be fetched here.'));
        }
        nodes.push(removeControls(article));
        view.replaceChildren(...nodes);
        updateAddButton();
    }
    // ---- right panel -----------------------------------------------------
    function excerptBlock(excerpt) {
        const block = make('div');
        block.append(make('blockquote', excerpt.excerpt_text));
        const checks = make('div', undefined, 'check-list');
        specialties.forEach(specialty => {
            const label = make('label', undefined, 'check-label');
            const box = make('input');
            box.type = 'checkbox';
            box.checked = excerpt.specialties.includes(specialty.id);
            box.dataset.excerptId = String(excerpt.id);
            box.dataset.specialty = specialty.id;
            box.addEventListener('change', () => { void saveSpecialties(excerpt.id, box.dataset.specialty || ''); });
            label.append(box, document.createTextNode(specialty.label));
            checks.append(label);
        });
        block.append(checks);
        const actions = make('div', undefined, 'card-actions');
        actions.append(button('Remove excerpt', 'btn btn-secondary', () => { void removeExcerpt(excerpt.id); }));
        block.append(actions);
        return block;
    }
    function renderRight() {
        const view = byId('excerptsView');
        if (current === null || current.kind !== 'saved') {
            view.replaceChildren(make('p', MESSAGE_NO_SELECTION));
            return;
        }
        const excerpts = current.article.excerpts || [];
        if (excerpts.length === 0) {
            view.replaceChildren(make('p', MESSAGE_NO_EXCERPTS));
            return;
        }
        view.replaceChildren(...excerpts.map(excerptBlock));
    }
    function renderAll() {
        renderMiddle();
        renderRight();
        renderResults();
        renderSaved();
    }
    // ---- actions ---------------------------------------------------------
    function showPreview(result) {
        current = { kind: 'preview', result };
        confirmingRemove = false;
        renderAll();
    }
    async function openSaved(id) {
        const reply = await call('GET', `/api/references/${id}`);
        if (!reply || !reply.article) {
            return;
        }
        specialties = reply.specialties || specialties;
        current = { kind: 'saved', article: reply.article };
        confirmingRemove = false;
        setStatus('');
        renderAll();
    }
    /** Show the article the server sent back, and bring the saved list up to date. */
    async function showReturned(article, rerenderMiddle) {
        current = { kind: 'saved', article };
        if (rerenderMiddle) {
            renderMiddle();
        }
        renderRight();
        await refreshSaved();
    }
    async function saveResult(result) {
        const reply = await call('POST', '/api/references', result);
        if (!reply || reply.id === undefined) {
            return;
        }
        result.saved_id = reply.id;
        await openSaved(reply.id);
        setStatus('Saved.');
        await refreshSaved();
    }
    async function fetchAbstract(id) {
        setStatus('Fetching…');
        const reply = await call('POST', `/api/references/${id}/abstract`);
        if (!reply || !reply.article) {
            return;
        }
        setStatus('Abstract fetched.');
        await showReturned(reply.article, true);
    }
    async function removeArticle(id) {
        const reply = await call('DELETE', `/api/references/${id}`);
        confirmingRemove = false;
        if (!reply) {
            renderMiddle();
            return;
        }
        (found || []).forEach(result => {
            if (result.saved_id === id) {
                result.saved_id = null;
            }
        });
        current = null;
        setStatus('Removed.');
        renderMiddle();
        renderRight();
        renderResults();
        await refreshSaved();
    }
    async function addExcerpt(id) {
        const text = selectedText;
        if (!text) {
            return;
        }
        const reply = await call('POST', `/api/references/${id}/excerpts`, { text });
        if (!reply || !reply.article) {
            return;
        }
        window.getSelection()?.removeAllRanges();
        setStatus('Excerpt added.');
        await showReturned(reply.article, true);
    }
    async function saveSpecialties(excerptId, changedSpecialty) {
        const boxes = Array.from(document.querySelectorAll('#excerptsView input[type="checkbox"]'))
            .filter(box => box.dataset.excerptId === String(excerptId));
        const chosen = boxes.filter(box => box.checked).map(box => box.dataset.specialty || '');
        const reply = await call('PUT', `/api/excerpts/${excerptId}`, { specialties: chosen });
        if (!reply || !reply.article) {
            return;
        }
        setStatus('Saved.');
        await showReturned(reply.article, false);
        const again = Array.from(document.querySelectorAll('#excerptsView input[type="checkbox"]'))
            .find(box => box.dataset.excerptId === String(excerptId) && box.dataset.specialty === changedSpecialty);
        again?.focus();
    }
    async function removeExcerpt(excerptId) {
        const reply = await call('DELETE', `/api/excerpts/${excerptId}`);
        if (!reply || !reply.article) {
            return;
        }
        setStatus('Excerpt removed.');
        await showReturned(reply.article, false);
    }
    document.addEventListener('DOMContentLoaded', () => {
        byId('lookupForm').addEventListener('submit', (event) => {
            event.preventDefault();
            void lookUp();
        });
        byId('savedFilter').addEventListener('input', renderSaved);
        document.addEventListener('selectionchange', updateAddButton);
        void refreshSaved();
    });
})();
