# Contributing to HeloWrite

PRs always welcome. If unsure about scope, just open an issue. 

Setup instructions are in the [README](README.md) — same as what you'd run to use the app, plus `pip install -e .[dev]` for dev dependencies.

A few pointers:

- **Format with `ruff`** before committing. Keeps things consistent.
- **Small functions**, one job each.
- Keep commits descriptive, for example `feat: new theme`.

PR process:

1. Branch from `main`
2. Make your changes
3. Run tests and make sure everything passes
4. Open a PR with a description of what and why

## The Heresy Check

Use whatever tools you want: IDEs, LLMs, typewriters, abacuses, arcane invocations. We don’t care. As long as you actually understand the code you’re shipping and it passes tests, we don't require an affidavit of manual labor or a signed testament of non-AI taint.

## Reporting Issues

Open a GitHub issue with steps to reproduce, your Python version and OS, and any error output.

## Feature Requests & Scope

Read the Markdown Scope section before opening a PR for a new feature. HeloWrite is a prose tool, not a formatting tool — saves you writing code for something we're not going to merge.

## License

Contributions are MIT-licensed, same as the project.
