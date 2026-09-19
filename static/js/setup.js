"use strict";
/**
 * Setup screen: the "Choose a folder" button opens the computer's own
 * folder picker through the server (which runs on this machine) and puts
 * the choice into the field. Typing a path still works without it.
 */
(function () {
    const button = document.getElementById('browseFolder');
    const input = document.getElementById('dataFolder');
    const status = document.getElementById('browseStatus');
    if (!button || !input) {
        return;
    }
    function say(message) {
        if (status) {
            status.textContent = message;
        }
    }
    button.addEventListener('click', async () => {
        button.setAttribute('disabled', '');
        say('Choose a folder in the window that opened.');
        try {
            const response = await fetch('/setup/browse', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ current: input.value }),
            });
            const data = (await response.json());
            if (data.folder) {
                input.value = data.folder;
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
            say('The folder picker could not open. Type the folder path instead.');
        }
        finally {
            button.removeAttribute('disabled');
        }
    });
})();
