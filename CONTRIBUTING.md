---
title: Contributing
description: Guidelines for contributing to the MAI-Voice podcast toolchain
---

## How to contribute

Contributions are welcome — bug fixes, new voice support, additional output formats, or documentation improvements.

## Getting started

1. Fork the repo and create a branch from `main`.
2. Follow the setup steps in [README.md](README.md) to get the pipeline running locally.
3. Make your changes, run the full pipeline end-to-end to verify nothing broke.

## Pull requests

- Keep changes focused — one logical change per PR.
- Update `README.md` or `docs/` if your change affects documented behaviour.
- If you add a new dependency, add it to `requirements.txt` with a minimum-version pin.

## Reporting issues

Open a GitHub Issue with:

- A short description of the problem.
- The command you ran and the full error output.
- Your OS, Python version, and ffmpeg version.

## Code style

- Python 3.10+.
- No formatting tool is enforced, but match the style of the existing files.
- Avoid adding dependencies that duplicate what `pydub`, `mutagen`, or `Pillow` already provide.

## Security

**Never commit `.env` or any file containing Azure keys.** The `.gitignore` already excludes `.env` but please double-check before pushing.

If you discover a security issue, open a private GitHub Security Advisory rather than a public issue.
