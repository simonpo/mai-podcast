"""Generate 80s Activision/Atari 2600 style cover art and package as MP3."""

import io
import json
import sys
from pathlib import Path

COVER_CONFIG_PATH = Path(__file__).parent / "cover.json"

DEFAULT_CONFIG = {
    "cover": {
        "studio_banner": "\u25b6  M A I - V O I C E  S T U D I O S  \u25b6",
        "exclamation": "WOAH",
        "subtitle": "IT'S THE",
        "show_title": "ISE PODCAST",
        "episode": "EPISODE 1!",
        "footer": "MAI-VOICE-1  \u2122  AZURE SPEECH SERVICES  \u00a92026",
    },
    "metadata": {
        "title": "ISE Podcast Episode 1",
        "subtitle": "",
        "artist": "MAI-Voice-1",
        "album": "ISE Podcast",
        "album_artist": "",
        "year": "",
        "track": "",
        "genre": "Podcast",
        "publisher": "",
        "author_url": "",
        "copyright": "",
        "comment": "",
        "podcast_feed_url": "",
    },
}


def load_cover_config(config_path: Path = COVER_CONFIG_PATH) -> dict:
    """Load cover.json, falling back to defaults for any missing keys."""
    config = {
        "cover": dict(DEFAULT_CONFIG["cover"]),
        "metadata": dict(DEFAULT_CONFIG["metadata"]),
    }
    if config_path.exists():
        with open(config_path, encoding="utf-8") as f:
            loaded = json.load(f)
        config["cover"].update(loaded.get("cover", {}))
        config["metadata"].update(loaded.get("metadata", {}))
    else:
        print(f"Warning: {config_path} not found, using defaults.", file=sys.stderr)
    return config

from PIL import Image, ImageDraw, ImageFont
from mutagen.id3 import (
    APIC, COMM, ID3, PCST, TALB, TCOP, TCON, TIT1, TIT2, TIT3,
    TPE1, TPE2, TPUB, TRCK, TYER, WFED, WOAR,
)
from mutagen.mp3 import MP3
from pydub import AudioSegment


def generate_cover_art(output_path: str = "output/cover.png", config: dict | None = None) -> str:
    """Generate 80s Activision-stripe style cover art."""
    if config is None:
        config = load_cover_config()
    cover = config["cover"]
    W, H = 3000, 3000
    img = Image.new("RGB", (W, H), "#000000")
    draw = ImageDraw.Draw(img)

    # === Activision-style horizontal rainbow stripes ===
    stripe_colors = [
        "#FF0000",  # red
        "#FF4400",  # red-orange
        "#FF8800",  # orange
        "#FFBB00",  # amber
        "#FFDD00",  # yellow
        "#CCFF00",  # yellow-green
        "#44FF00",  # green
        "#00DDAA",  # teal
        "#0088FF",  # blue
        "#4400FF",  # indigo
        "#8800CC",  # purple
        "#CC0088",  # magenta
    ]

    # Top stripes section (Activision box top)
    stripe_start = 60
    stripe_height = 28
    stripe_gap = 4
    for i, color in enumerate(stripe_colors):
        y = stripe_start + i * (stripe_height + stripe_gap)
        draw.rectangle([0, y, W, y + stripe_height], fill=color)

    stripe_end = stripe_start + len(stripe_colors) * (stripe_height + stripe_gap)

    # === Main "screen" area — dark blue gradient feel ===
    screen_top = stripe_end + 30
    screen_bottom = H - 320
    screen_left = 80
    screen_right = W - 80

    # Dark gradient background for the screen
    for y in range(screen_top, screen_bottom):
        ratio = (y - screen_top) / (screen_bottom - screen_top)
        r = int(10 + 20 * ratio)
        g = int(5 + 15 * ratio)
        b = int(40 + 60 * ratio)
        draw.line([(screen_left, y), (screen_right, y)], fill=(r, g, b))

    # Screen border — bright blue glow
    for offset in range(4):
        alpha = 255 - offset * 50
        color = (0, min(255, 100 + offset * 40), 255)
        draw.rectangle(
            [screen_left - offset, screen_top - offset,
             screen_right + offset, screen_bottom + offset],
            outline=color, width=1,
        )

    # === Scanlines effect on the screen ===
    for y in range(screen_top, screen_bottom, 3):
        draw.line([(screen_left, y), (screen_right, y)], fill=(0, 0, 0, 40), width=1)

    # === Grid lines (Tron-style perspective) ===
    grid_color = (0, 80, 180)
    # Horizontal grid lines
    for i in range(8):
        y = screen_top + 100 + i * 50
        if y < screen_bottom:
            draw.line([(screen_left + 20, y), (screen_right - 20, y)], fill=grid_color, width=1)
    # Vertical grid lines converging
    cx = W // 2
    for i in range(-6, 7):
        x_top = cx + i * 30
        x_bot = cx + i * 80
        if screen_left < x_bot < screen_right:
            draw.line(
                [(x_top, screen_top + 80), (x_bot, screen_bottom - 20)],
                fill=grid_color, width=1,
            )

    # === Stars in the screen ===
    import random
    random.seed(42)
    for _ in range(60):
        x = random.randint(screen_left + 10, screen_right - 10)
        y = random.randint(screen_top + 10, screen_bottom - 10)
        brightness = random.randint(150, 255)
        size = random.choice([1, 1, 1, 2])
        draw.ellipse([x, y, x + size, y + size], fill=(brightness, brightness, brightness))

    # === Bottom stripes (mirror of top) ===
    bottom_stripe_start = H - 280
    for i, color in enumerate(reversed(stripe_colors)):
        y = bottom_stripe_start + i * (stripe_height + stripe_gap)
        draw.rectangle([0, y, W, y + stripe_height], fill=color)

    # === Text — use built-in fonts with 80s feel ===
    # Title text
    try:
        # Try to find a bold/impact font on the system
        title_font = ImageFont.truetype("impact.ttf", 72)
        sub_font = ImageFont.truetype("impact.ttf", 42)
        small_font = ImageFont.truetype("arial.ttf", 28)
    except OSError:
        title_font = ImageFont.load_default()
        sub_font = title_font
        small_font = title_font

    # "WOAH" — big chrome/neon text
    woah_text = cover["exclamation"]
    bbox = draw.textbbox((0, 0), woah_text, font=title_font)
    tw = bbox[2] - bbox[0]
    x = (W - tw) // 2

    # Glow effect
    for offset in range(6, 0, -1):
        glow_alpha = 60 + offset * 20
        draw.text(
            (x - offset, screen_top + 60 - offset),
            woah_text, font=title_font,
            fill=(255, 0, min(255, glow_alpha + 100)),
        )
    # Chrome gradient text (simulated)
    draw.text((x + 2, screen_top + 62), woah_text, font=title_font, fill=(80, 0, 80))
    draw.text((x, screen_top + 60), woah_text, font=title_font, fill=(255, 50, 255))

    # subtitle line
    its_text = cover["subtitle"]
    bbox = draw.textbbox((0, 0), its_text, font=sub_font)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) // 2, screen_top + 155), its_text, font=sub_font, fill=(0, 255, 255))

    # show title — big and bright
    pod_text = cover["show_title"]
    try:
        pod_font = ImageFont.truetype("impact.ttf", 96)
    except OSError:
        pod_font = title_font
    bbox = draw.textbbox((0, 0), pod_text, font=pod_font)
    tw = bbox[2] - bbox[0]
    px = (W - tw) // 2

    # Yellow glow
    for offset in range(4, 0, -1):
        draw.text(
            (px - offset, screen_top + 215 - offset),
            pod_text, font=pod_font, fill=(180, 180, 0),
        )
    draw.text((px + 2, screen_top + 217), pod_text, font=pod_font, fill=(100, 80, 0))
    draw.text((px, screen_top + 215), pod_text, font=pod_font, fill=(255, 255, 0))

    # episode line
    ep_text = cover["episode"]
    bbox = draw.textbbox((0, 0), ep_text, font=sub_font)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) // 2 + 2, screen_top + 340 + 2), ep_text, font=sub_font, fill=(100, 0, 0))
    draw.text(((W - tw) // 2, screen_top + 340), ep_text, font=sub_font, fill=(255, 80, 0))

    # === Bottom label — Activision-style ===
    label_y = H - 60
    label_text = cover["footer"]
    bbox = draw.textbbox((0, 0), label_text, font=small_font)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) // 2, label_y), label_text, font=small_font, fill=(200, 200, 200))

    # === Activision logo stripe at very top ===
    draw.rectangle([0, 0, W, 50], fill="#1a1a2e")
    try:
        top_font = ImageFont.truetype("impact.ttf", 32)
    except OSError:
        top_font = small_font
    top_text = cover["studio_banner"]
    bbox = draw.textbbox((0, 0), top_text, font=top_font)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) // 2, 8), top_text, font=top_font, fill=(255, 255, 255))

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(out), "PNG")
    print(f"Cover art saved to {out.resolve()}")
    return str(out)


def wav_to_mp3_with_art(
    wav_path: str,
    cover_path: str,
    mp3_path: str,
    config: dict | None = None,
) -> None:
    """Convert WAV to MP3 and embed cover art + metadata from config."""
    if config is None:
        config = load_cover_config()
    meta = config["metadata"]

    # Convert WAV to MP3.
    # Azure TTS outputs 48 kHz mono; duplicate to stereo for podcast compatibility.
    # 48 kHz is accepted natively by Apple Podcasts and Spotify — no resampling needed.
    audio = AudioSegment.from_wav(wav_path)
    audio = audio.set_channels(2)
    audio.export(mp3_path, format="mp3", bitrate="192k")
    print(f"MP3 created: {mp3_path} (48 kHz stereo, 192 kbps)")

    # Add ID3 tags + cover art
    mp3 = MP3(mp3_path, ID3=ID3)
    try:
        mp3.add_tags()
    except Exception:
        pass

    def _set(frame, value: str) -> None:
        """Add a text frame only when value is non-empty."""
        if value and value.strip():
            mp3.tags.add(frame)

    # Required fields
    mp3.tags.add(TIT2(encoding=3, text=[meta["title"]]))
    mp3.tags.add(TPE1(encoding=3, text=[meta["artist"]]))
    mp3.tags.add(TALB(encoding=3, text=[meta["album"]]))
    mp3.tags.add(TCON(encoding=3, text=[meta.get("genre", "Podcast")]))

    # Optional text frames — only written when non-empty
    _set(TIT3(encoding=3, text=[meta.get("subtitle", "")]),       meta.get("subtitle", ""))
    _set(TPE2(encoding=3, text=[meta.get("album_artist", "")]),   meta.get("album_artist", ""))
    _set(TYER(encoding=3, text=[meta.get("year", "")]),           meta.get("year", ""))
    _set(TRCK(encoding=3, text=[meta.get("track", "")]),          meta.get("track", ""))
    _set(TPUB(encoding=3, text=[meta.get("publisher", "")]),      meta.get("publisher", ""))
    _set(TCOP(encoding=3, text=[meta.get("copyright", "")]),      meta.get("copyright", ""))
    # TIT1 mirrors album_artist as the content-group/show field recognised by some players
    _set(TIT1(encoding=3, text=[meta.get("album_artist", "")]),   meta.get("album_artist", ""))

    # Comment frame (iTunes reads this as episode description)
    if meta.get("comment", "").strip():
        mp3.tags.add(COMM(encoding=3, lang="eng", desc="", text=[meta["comment"]]))

    # URL link frames
    if meta.get("author_url", "").strip():
        mp3.tags.add(WOAR(url=meta["author_url"]))
    if meta.get("podcast_feed_url", "").strip():
        mp3.tags.add(WFED(url=meta["podcast_feed_url"]))

    # iTunes podcast flag — marks file as a podcast in Apple Podcasts
    mp3.tags.add(PCST(encoding=0, text=["1"]))

    # Convert cover to JPEG — Windows Media Player prefers it
    cover_img = Image.open(cover_path)
    jpeg_buf = io.BytesIO()
    cover_img.convert("RGB").save(jpeg_buf, format="JPEG", quality=95)
    cover_data = jpeg_buf.getvalue()

    mp3.tags.add(
        APIC(
            encoding=3,
            mime="image/jpeg",
            type=3,  # Cover (front)
            desc="Cover",
            data=cover_data,
        )
    )
    # Save as ID3v2.3 for broad compatibility (Windows Media Player)
    mp3.save(v2_version=3)
    print(f"Embedded cover art and metadata into {mp3_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python package_mp3.py <input.wav> [output.mp3]")
        sys.exit(1)

    wav = sys.argv[1]
    mp3 = sys.argv[2] if len(sys.argv) > 2 else wav.replace(".wav", ".mp3")

    cfg = load_cover_config()
    cover = generate_cover_art("output/cover.png", config=cfg)
    wav_to_mp3_with_art(wav, cover, mp3, config=cfg)
    print(f"\nDone! {mp3}")
