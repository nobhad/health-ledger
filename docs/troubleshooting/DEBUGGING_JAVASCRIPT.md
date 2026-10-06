# Debugging JavaScript

The pages' scripts are TypeScript in `static/js/*.ts`, compiled in place to
`.js` by `npm run build`. Edit the `.ts`; the browser loads the `.js`.

## The console

Open the browser's developer tools (F12 in Chrome, Edge and Firefox;
Cmd+Option+C in Safari) and choose the Console tab. The Network tab shows each
request a page makes to the app, and its response.

To try an API route from the console:

```javascript
fetch('/api/all-genes').then(r => r.json()).then(console.log)
```

## The debug helpers

`static/js/debug.ts` defines logging helpers on `window`. Only the **Query**
page loads `debug.js`, so they exist there and not on the other pages.

| Helper | Logs |
| --- | --- |
| `debugLog(message, ...args)` | A DEBUG line |
| `infoLog(message, ...args)` | An INFO line |
| `warnLog(message, ...args)` | A warning |
| `errorLog(message, error, ...args)` | An error, with its stack trace |
| `perfLog(operation, startTime)` | How long since `startTime` (from `performance.now()`) |
| `apiLog(method, url, data, response)` | A request and its response |
| `stateLog(name, oldValue, newValue)` | A change of state |
| `elementLog(name, action, data)` | Something done to an element |

Lines look like `[2026-10-05T12:00:00.000Z DEBUG] message`.

Settings live in `window.GENETIC_PROFILE_DEBUG`: `enabled`, `logLevel`
(`DEBUG`, `INFO`, `WARN` or `ERROR`), `showTimestamps` and `showStackTraces`.
All are on by default, with the level at `DEBUG`. In the console:

```javascript
window.GENETIC_PROFILE_DEBUG.enabled = false
window.GENETIC_PROFILE_DEBUG.logLevel = 'WARN'
```

`window.initDebugPanel()` adds a small panel with an enable box, a level
selector and a **Clear Console** button. Nothing calls it for you.

## Errors from browser extensions

An error whose file name is a browser extension's own script (names like
content_script or installHook, which are not in this app) comes from a
browser extension, not from Health Ledger. The Query page hides console errors
and warnings that mention either name. On other pages, filter them out in the
console's filter box, for example by typing a minus sign and that name.

## The Query page

If the dropdowns stay empty:

1. Check the console for a red line from `query.js` or `multiselect.js`. Both
   scripts print a "loaded successfully" line when they start.
2. Check that `/api/all-genes`, `/api/all-conditions` and `/api/all-traits`
   return arrays, in the Network tab or with the `fetch` line above.
3. Check that the file exists: `static/js/query.js` and
   `static/js/multiselect.js`. If they do not, run `npm run build`.

## The References page

It shows a message under the search box when a request fails. "The app did not
answer. Is it still running?" means the server stopped or the address is wrong;
look at the terminal or `logs/app.log`. Any other message is the app's own
sentence about what went wrong, and is explained in
[REFERENCES.md](../features/REFERENCES.md) and
[COMMON_ISSUES.md](COMMON_ISSUES.md).
