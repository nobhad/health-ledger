# Contributing

Health Ledger is a personal project published so people can read it and run
it. Patches are welcome; please read this first so neither of us wastes time.

## Before you write code

Open an issue and describe what you want to change. For anything larger than a
bug fix, wait for a reply — the roadmap in `CURRENT_WORK.md` is deliberately
ordered, and a change that jumps it may not be merged however good it is.

Two things will be declined on sight, so please do not spend time on them:

- Anything that sends data off the machine — analytics, crash reporting,
  update checks, cloud sync, an account system.
- Design, layout or CSS changes that were not asked for.

## Before you open a pull request

```bash
./venv/bin/python -m pytest              # all tests pass
npm run check                            # lint + typecheck clean
python3 scripts/check_private_data.py    # no private data
```

All three run in CI and a red one will not be merged.

## The rules that matter most

- **Never commit private data.** No real names, record file names, home
  paths, dates of birth, genotypes or results — in code, tests, fixtures,
  docs or commit messages. Use placeholders. The scanner above enforces it and
  so does a pre-commit hook.
- **Never edit a `.js` file that has a `.ts` sibling.** Edit the TypeScript;
  `npm run build` compiles it.
- **Never hand-edit `static/css/design-system/`.** It is vendored. Run
  `npm run sync:design-system`.
- **No literal colours, sizes or durations in app CSS.** Add a token to
  `app-tokens.css` aliasing a design-system token, then use it.
- **No hardcoding** generally: URLs, ports and keys are environment
  variables; magic numbers get names; paths go through `pathlib`.
- **Resource paths go through `config.BASE_DIR`, never `__file__`**, or the
  packaged build breaks. See
  [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md#paths-and-the-packaged-build).

[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) has the rest — project structure,
the layout contract, and how the packaged build differs from a checkout.

## Licence and your contribution

The project is source-available, not open source: read
[LICENSE](LICENSE) before you start, particularly §3 on redistribution and
commercial use, and §4, which is the bit that applies to you.

In short: sending a patch grants me a perpetual, royalty-free licence to use
and relicense it as part of Health Ledger. You keep your own copyright in what
you wrote. If that is not acceptable, please do not send code — an issue
describing the problem is still very welcome.

## Reporting a security problem

Privately, not as an issue. See [SECURITY.md](SECURITY.md).
