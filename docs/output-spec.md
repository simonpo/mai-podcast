---
title: "Output Format Specification"
description: "Technical rationale for the audio, metadata, and cover art formats produced by the MAI Voice Podcast Studio pipeline."
author: "ISE"
ms.date: "2026-05-13"
ms.topic: "reference"
keywords: ["podcast", "mp3", "id3", "audio", "specification", "apple-podcasts", "spotify"]
---

## Audio format

### Intermediate WAV files

Azure TTS is requested in `riff-48khz-16bit-mono-pcm` format. This is the native
high-fidelity output rate for MAI-Voice-1 voices (indicated by the `IsHighQuality48K`
flag in the voices list API). Requesting 48 kHz avoids any server-side resampling and
preserves the full quality of the synthesis model.

The jingle generator (`add_jingle.py`) reads the sample rate from the WAV header at
runtime and matches it, so all WAV files in the pipeline stay at 48 kHz throughout.

### Final MP3

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Sample rate | 48 kHz | Matches the WAV source; no resampling degradation. Apple Podcasts and Spotify both accept 48 kHz natively. |
| Channels | Stereo (2) | Mono-to-stereo duplication applied by pydub during export. Stereo is the expected format for podcast distribution and displays correctly in all players. |
| Bitrate | 192 kbps | Above the 128 kbps floor required by Apple and Spotify. Transparent quality for speech content. 256+ kbps offers no audible benefit for voice-only audio. |
| ID3 version | ID3v2.3 | Version 2.4 is technically newer but version 2.3 has broader compatibility across media players, including Windows Media Player and older iTunes builds. mutagen's `v2_version=3` parameter enforces this. |

> [!NOTE]
> 44.1 kHz is the traditional music standard but is not required by podcast platforms.
> Azure can produce 44.1 kHz output, but does so by downsampling internally from 48 kHz.
> Requesting 48 kHz directly and staying at that rate is the higher-quality path.

## ID3 metadata tags

The following ID3v2.3 frames are written to the MP3. Optional fields are skipped
entirely if left blank in `cover.json`, keeping the tag block clean.

### Always written

| Frame | Field in cover.json | Purpose |
|-------|---------------------|---------|
| `TIT2` | `metadata.title` | Episode title. Displayed by all podcast clients. |
| `TPE1` | `metadata.artist` | Episode artist / host name. |
| `TALB` | `metadata.album` | Show name. Used by Apple Podcasts and Spotify to group episodes. |
| `TCON` | `metadata.genre` | Genre. Set to `Podcast` by default, which triggers podcast-specific UI in some players. |
| `PCST` | (always `1`) | iTunes podcast flag. Marks the file as a podcast episode in Apple Podcasts and compatible players. |
| `APIC` | cover art image | Front cover art, embedded as JPEG inside the MP3. Windows Media Player requires JPEG rather than PNG, so the PNG is converted at embed time. |

### Written when non-empty

| Frame | Field in cover.json | Purpose |
|-------|---------------------|---------|
| `TIT3` | `metadata.subtitle` | Episode subtitle or short description. Shown beneath the title in some clients. |
| `TPE2` | `metadata.album_artist` | Album/show-level artist, distinct from per-episode artist. Used by iTunes to correctly group a podcast series. |
| `TYER` | `metadata.year` | Publication year. |
| `TRCK` | `metadata.track` | Episode number. |
| `TPUB` | `metadata.publisher` | Publishing organisation or network. |
| `TCOP` | `metadata.copyright` | Copyright statement. |
| `TIT1` | `metadata.album_artist` | Content group / show series. Mirrors album_artist; recognised as a show grouping field by some players. |
| `COMM` | `metadata.comment` | Free-text comment / episode description. iTunes reads this field as the episode description when no RSS feed is present. |
| `WOAR` | `metadata.author_url` | URL link frame pointing to the author or show website. |
| `WFED` | `metadata.podcast_feed_url` | iTunes podcast feed URL. When present, Apple Podcasts can offer a direct subscribe link from the file itself. |

## Cover art

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Dimensions | 3000×3000 px | Apple Podcasts requires a minimum of 1400×1400 and recommends 3000×3000 for full-resolution display on retina screens. Spotify also uses 3000×3000 as the preferred upload size. |
| Format | PNG (source), JPEG (embedded) | PNG is used as the source file to preserve quality. It is converted to JPEG at embed time because Windows Media Player and some older ID3 readers have poor support for PNG cover art in APIC frames. |
| JPEG quality | 95 | High enough that compression artefacts are invisible at normal cover art display sizes. |
| Colour space | RGB | Required by both JPEG and the podcast platform validators. |

### Design

The cover art uses a procedurally generated 80s Activision/Atari 2600 aesthetic:

- Rainbow horizontal stripes at top and bottom (mirrored), referencing the Activision cartridge label style.
- A dark blue gradient "screen" area with a Tron-style perspective grid and randomised starfield.
- Neon glow text rendered in Impact (falling back to the PIL default font when Impact is unavailable).
- A studio banner bar at the very top.

All text content is read from `cover.json` so the design can be customised per show and per episode without touching Python code.
