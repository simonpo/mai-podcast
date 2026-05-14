---
title: Changelog
description: Release history for the MAI-Voice podcast toolchain
---

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.0.0] - 2026-05-13

Initial public release.

### Added

- `synthesize.py` — converts `.txt` or `.json` scripts to WAV using Azure MAI-Voice-1 voices via the TTS REST API
- `add_jingle.py` — wraps speech audio with a synthesised retro intro jingle and doom-style outro
- `package_mp3.py` — generates 3000×3000 retro cover art, converts WAV to 192 kbps stereo MP3, and embeds full ID3v2.3 metadata
- `cover.json` — JSON config file for all cover art text and ID3 metadata fields; no Python editing required per episode
- `scripts/podcast-demo.txt` — plain-text script demo with `[IRIS]` / `[GRANT]` speaker tags
- `scripts/dialogue-demo.json` — JSON script demo with explicit SSML fields
- `assets/cover-example.png` — 3000×3000 example cover art committed to the repo
- `docs/output-spec.md` — technical rationale for all audio and packaging format choices
- `.github/agents/mai-podcast.agent.md` — GitHub Copilot agent for guided end-to-end podcast production
- `README.md`, `CONTRIBUTING.md`, `LICENSE` (MIT), `.env.example`

### Audio pipeline

- Azure TTS output format: `riff-48khz-16bit-mono-pcm` (48 kHz native, no resampling)
- MP3: 48 kHz, stereo (mono → stereo via pydub), 192 kbps, ID3v2.3
- ID3 tags written: `TIT2`, `TIT3`, `TPE1`, `TPE2`, `TALB`, `TCON`, `TCOP`, `TYER`, `TIT1`, `TPUB`, `TRCK`, `COMM`, `PCST`, `WOAR`, `WFED`, `APIC`
- Cover art: 3000×3000 PNG (Activision/Atari retro style), converted to JPEG quality 95 for the `APIC` frame

### Voices supported

`en-US-Iris:MAI-Voice-1`, `en-US-Grant:MAI-Voice-1`, `en-US-Jasper:MAI-Voice-1`, `en-US-June:MAI-Voice-1`
