/**
 * System dialogs for path fields.
 *
 * A button with data-browse="folder" or data-browse="save" and
 * data-target="<input id>" asks the server, which runs on this machine, to
 * open the computer's own dialog and puts the choice into the field. An
 * optional data-status="<element id>" names where to say what is happening,
 * and data-filename-from="<select id>" derives the proposed file name's
 * extension from a format select. Typing a path still works without any
 * of this.
 */
(function (): void {
    const buttons = document.querySelectorAll<HTMLButtonElement>('[data-browse]');
    if (buttons.length === 0) {
        return;
    }

    buttons.forEach((button) => {
        const target = document.getElementById(button.dataset.target ?? '') as HTMLInputElement | null;
        if (!target) {
            return;
        }
        const status = document.getElementById(button.dataset.status ?? '');
        const formatSelect = document.getElementById(button.dataset.filenameFrom ?? '') as HTMLSelectElement | null;
        const kind = button.dataset.browse === 'save' ? 'save' : 'folder';

        const say = (message: string): void => {
            if (status) {
                status.textContent = message;
            }
        };

        button.addEventListener('click', async () => {
            button.setAttribute('disabled', '');
            say(kind === 'save' ? 'Choose where to save in the window that opened.' : 'Choose a folder in the window that opened.');
            try {
                const current = target.value;
                const extension = formatSelect ? formatSelect.value : '';
                const base = current.split('/').pop()?.split('\\').pop() || 'export';
                const stem = base.includes('.') ? base.slice(0, base.lastIndexOf('.')) : base;
                const filename = extension ? `${stem}.${extension}` : base;
                const response = await fetch('/api/browse', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ kind, current, filename }),
                });
                const data = (await response.json()) as { path?: string | null; error?: string };
                if (data.path) {
                    target.value = data.path;
                    target.dispatchEvent(new Event('change', { bubbles: true }));
                    say('');
                } else if (data.error) {
                    say(data.error);
                } else {
                    say('');
                }
            } catch (error) {
                say('The dialog could not open. Type the path instead.');
            } finally {
                button.removeAttribute('disabled');
            }
        });
    });
})();
