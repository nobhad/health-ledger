# Vendored design system

Copied from no-bhad-codes at commit d3c21c8f (2026-09-19 22:39:42 -0400) by `scripts/sync_design_system.sh`.
Do not edit these files by hand. Re-run the script to update.

Contents: `tokens/` (the 11 token files plus `portal-theme.css`), `index.css`,
`layer-order.css`, `reset.css`, `fonts.css`. Fonts live in `static/fonts/`.

Patches applied on copy (see the script): font URLs use `/static/fonts/`, and the
portal surface selector `[data-page="client"]` is renamed to `[data-page="ledger"]`.

Health Ledger's own stylesheets live beside this directory and only ever
reference tokens defined here.
