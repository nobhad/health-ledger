// References page: look journal articles up, save them, and choose the
// passages of their abstracts that go into a specialist's document.
//
// Everything that comes from the server or the person is put into the page
// with textContent or createElement, never built into an HTML string. The whole
// file is one function because static/js is compiled as global scripts and a
// top-level name here would collide with the other pages' scripts.

(function (): void {
    interface Excerpt {
        id: number;
        excerpt_text: string;
        specialties: string[];
    }

    interface SavedArticle {
        id: number;
        title: string;
        authors?: string | null;
        journal?: string | null;
        year?: number | null;
        pubmed_id?: string | null;
        doi?: string | null;
        url?: string | null;
        abstract?: string | null;
        has_abstract?: boolean;
        excerpt_count?: number;
        excerpts?: Excerpt[];
    }

    interface SearchResult {
        title: string;
        authors?: string | null;
        journal?: string | null;
        year?: number | null;
        pubmed_id?: string | null;
        doi?: string | null;
        url?: string | null;
        abstract?: string | null;
        cited_by?: number | null;
        kind?: string | null;
        saved_id: number | null;
    }

    interface Specialty {
        id: string;
        label: string;
    }

    interface ApiReply {
        success: boolean;
        message?: string;
        results?: SearchResult[];
        articles?: SavedArticle[];
        article?: SavedArticle;
        specialties?: Specialty[];
        id?: number;
    }

    type Open =
        | { kind: 'saved'; article: SavedArticle }
        | { kind: 'preview'; result: SearchResult }
        | null;

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

    let found: SearchResult[] | null = null;
    let saved: SavedArticle[] = [];
    let specialties: Specialty[] = [];
    let current: Open = null;
    let confirmingRemove = false;
    let selectedText = '';
    let addButton: HTMLButtonElement | null = null;

    function byId<T extends HTMLElement>(id: string): T {
        return document.getElementById(id) as T;
    }

    function make<K extends keyof HTMLElementTagNameMap>(
        tag: K, text?: string, className?: string
    ): HTMLElementTagNameMap[K] {
        const node = document.createElement(tag);
        if (text !== undefined) {
            node.textContent = text;
        }
        if (className) {
            node.className = className;
        }
        return node;
    }

    function button(label: string, className: string, onClick: () => void): HTMLButtonElement {
        const node = make('button', label, className);
        node.type = 'button';
        node.addEventListener('click', onClick);
        return node;
    }

    function joinParts(parts: Array<string | number | null | undefined>): string {
        return parts
            .filter((part): part is string | number => part !== null && part !== undefined && part !== '')
            .join(META_SEPARATOR);
    }

    function setStatus(message: string, isError = false): void {
        const status = byId<HTMLElement>('referencesStatus');
        status.textContent = message;
        status.classList.toggle('is-error', isError);
    }

    /** Ask the app; on any failure show its sentence and answer null. */
    async function call(method: string, url: string, body?: object): Promise<ApiReply | null> {
        const options: RequestInit = { method };
        if (method !== 'GET') {
            options.headers = { 'Content-Type': 'application/json' };
            options.body = JSON.stringify(body ?? {});
        }
        let reply: ApiReply;
        try {
            const response = await fetch(url, options);
            reply = await response.json() as ApiReply;
        } catch (_error) {
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

    function listRow(title: string, meta: string, extra: string, active: boolean, open: () => void): HTMLLIElement {
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
        row.addEventListener('keydown', (event: KeyboardEvent) => {
            if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                open();
            }
        });
        return row;
    }

    function messageRow(text: string): HTMLLIElement {
        return make('li', text, 'sources-list-item is-empty');
    }

    function openSavedId(): number | null {
        return current && current.kind === 'saved' ? current.article.id : null;
    }

    function renderResults(): void {
        const heading = byId<HTMLElement>('resultsHeading');
        const list = byId<HTMLElement>('resultsList');
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
                } else {
                    showPreview(result);
                }
            });
        }));
    }

    function excerptCountText(count: number | undefined): string {
        if (!count) {
            return '';
        }
        return `${count} ${count === 1 ? 'excerpt' : 'excerpts'}`;
    }

    function renderSaved(): void {
        const list = byId<HTMLElement>('savedList');
        if (saved.length === 0) {
            list.replaceChildren(messageRow(MESSAGE_NOTHING_SAVED));
            return;
        }
        const needle = byId<HTMLInputElement>('savedFilter').value.trim().toLowerCase();
        const shown = saved.filter(article => !needle
            || [article.title, article.authors, article.journal]
                .some(field => (field || '').toLowerCase().includes(needle)));
        if (shown.length === 0) {
            list.replaceChildren(messageRow(MESSAGE_NO_MATCH));
            return;
        }
        const openId = openSavedId();
        list.replaceChildren(...shown.map(article => listRow(
            article.title,
            joinParts([article.journal, article.year, excerptCountText(article.excerpt_count)]),
            '',
            article.id === openId,
            () => { void openSaved(article.id); }
        )));
    }

    async function refreshSaved(): Promise<void> {
        const reply = await call('GET', '/api/references');
        if (reply && reply.articles) {
            saved = reply.articles;
            renderSaved();
        }
    }

    async function lookUp(): Promise<void> {
        const term = byId<HTMLInputElement>('lookupTerm').value.trim();
        if (!term) {
            setStatus('Type a gene, condition or medication first.', true);
            return;
        }
        const lookupBtn = byId<HTMLButtonElement>('lookupBtn');
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
    function articleAddress(article: SavedArticle | SearchResult): string {
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

    function articleHead(article: SavedArticle | SearchResult): HTMLElement[] {
        const nodes: HTMLElement[] = [make('h3', article.title)];
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

    function abstractParagraphs(text: string, id?: string): HTMLElement {
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

    function updateAddButton(): void {
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

    function removeControls(article: SavedArticle): HTMLElement {
        const row = make('div', undefined, 'card-actions');
        if (!confirmingRemove) {
            row.append(button('Remove article', 'btn btn-secondary', () => {
                confirmingRemove = true;
                renderMiddle();
            }));
            return row;
        }
        row.append(
            make('span', 'Remove this article and its excerpts?'),
            button('Remove', 'btn btn-secondary', () => { void removeArticle(article.id); }),
            button('Keep', 'btn btn-secondary', () => {
                confirmingRemove = false;
                renderMiddle();
            })
        );
        return row;
    }

    function renderMiddle(): void {
        const view = byId<HTMLElement>('articleView');
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
        } else if (article.pubmed_id) {
            nodes.push(make('p', 'The abstract has not been fetched yet. Fetching it sends this article\'s PubMed id to Europe PMC.'));
            const actions = make('div', undefined, 'card-actions');
            actions.append(button('Fetch abstract', 'btn btn-primary', () => { void fetchAbstract(article.id); }));
            nodes.push(actions);
        } else {
            nodes.push(make('p', 'This article has no PubMed id, so its abstract cannot be fetched here.'));
        }
        nodes.push(removeControls(article));
        view.replaceChildren(...nodes);
        updateAddButton();
    }

    // ---- right panel -----------------------------------------------------

    function excerptBlock(excerpt: Excerpt): HTMLElement {
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

    function renderRight(): void {
        const view = byId<HTMLElement>('excerptsView');
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

    function renderAll(): void {
        renderMiddle();
        renderRight();
        renderResults();
        renderSaved();
    }

    // ---- actions ---------------------------------------------------------

    function showPreview(result: SearchResult): void {
        current = { kind: 'preview', result };
        confirmingRemove = false;
        renderAll();
    }

    async function openSaved(id: number): Promise<void> {
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
    async function showReturned(article: SavedArticle, rerenderMiddle: boolean): Promise<void> {
        current = { kind: 'saved', article };
        if (rerenderMiddle) {
            renderMiddle();
        }
        renderRight();
        await refreshSaved();
    }

    async function saveResult(result: SearchResult): Promise<void> {
        const reply = await call('POST', '/api/references', result);
        if (!reply || reply.id === undefined) {
            return;
        }
        result.saved_id = reply.id;
        await openSaved(reply.id);
        setStatus('Saved.');
        await refreshSaved();
    }

    async function fetchAbstract(id: number): Promise<void> {
        setStatus('Fetching…');
        const reply = await call('POST', `/api/references/${id}/abstract`);
        if (!reply || !reply.article) {
            return;
        }
        setStatus('Abstract fetched.');
        await showReturned(reply.article, true);
    }

    async function removeArticle(id: number): Promise<void> {
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

    async function addExcerpt(id: number): Promise<void> {
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

    async function saveSpecialties(excerptId: number, changedSpecialty: string): Promise<void> {
        const boxes = Array.from(document.querySelectorAll<HTMLInputElement>('#excerptsView input[type="checkbox"]'))
            .filter(box => box.dataset.excerptId === String(excerptId));
        const chosen = boxes.filter(box => box.checked).map(box => box.dataset.specialty || '');
        const reply = await call('PUT', `/api/excerpts/${excerptId}`, { specialties: chosen });
        if (!reply || !reply.article) {
            return;
        }
        setStatus('Saved.');
        await showReturned(reply.article, false);
        const again = Array.from(document.querySelectorAll<HTMLInputElement>('#excerptsView input[type="checkbox"]'))
            .find(box => box.dataset.excerptId === String(excerptId) && box.dataset.specialty === changedSpecialty);
        again?.focus();
    }

    async function removeExcerpt(excerptId: number): Promise<void> {
        const reply = await call('DELETE', `/api/excerpts/${excerptId}`);
        if (!reply || !reply.article) {
            return;
        }
        setStatus('Excerpt removed.');
        await showReturned(reply.article, false);
    }

    document.addEventListener('DOMContentLoaded', () => {
        byId<HTMLFormElement>('lookupForm').addEventListener('submit', (event: Event) => {
            event.preventDefault();
            void lookUp();
        });
        byId<HTMLInputElement>('savedFilter').addEventListener('input', renderSaved);
        document.addEventListener('selectionchange', updateAddButton);
        void refreshSaved();
    });
})();
