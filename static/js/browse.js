"use strict";
/**
 * System dialogs for path fields.
 *
 * A button with data-browse="folder" or data-browse="save" and
 * data-target="<input id>" asks the server, which runs on this machine, to
 * open the computer's own dialog and puts the choice into the field. An
 * optional data-status="<element id>" names where to say what is happening,
 * and data-filename-from="<select id>" derives the proposed file name's
 * extension from a format select.
 *
 * When the field itself is hidden and the choice is shown as a sentence
 * instead, data-echo-path and data-echo-name name the elements that carry
 * the full path and the folder's own name, and data-echo-clear names a
 * clause that was only true of the folder proposed at the start ("in your
 * home folder") and must go once another one is picked.
 */
(function () {
    const buttons = document.querySelectorAll('[data-browse]');
    if (buttons.length === 0) {
        return;
    }
    buttons.forEach((button) => {
        const target = document.getElementById(button.dataset.target ?? '');
        if (!target) {
            return;
        }
        const status = document.getElementById(button.dataset.status ?? '');
        const echoPath = document.getElementById(button.dataset.echoPath ?? '');
        const echoName = document.getElementById(button.dataset.echoName ?? '');
        const echoClear = document.getElementById(button.dataset.echoClear ?? '');
        const formatSelect = document.getElementById(button.dataset.filenameFrom ?? '');
        const kind = button.dataset.browse === 'save' ? 'save' : 'folder';
        const say = (message) => {
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
                const data = (await response.json());
                if (data.path) {
                    target.value = data.path;
                    if (echoPath) {
                        echoPath.textContent = data.path;
                    }
                    if (echoName) {
                        echoName.textContent =
                            data.path.split('/').pop()?.split('\\').pop() || data.path;
                    }
                    if (echoClear) {
                        echoClear.remove();
                    }
                    target.dispatchEvent(new Event('change', { bubbles: true }));
                    say('');
                }
                else if (data.error) {
                    say(data.error);
                }
                else {
                    say('');
                }
            }
            catch (error) {
                say('The dialog could not open. Type the path instead.');
            }
            finally {
                button.removeAttribute('disabled');
            }
        });
    });
})();
