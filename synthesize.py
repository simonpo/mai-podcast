"""
MAI-Voice-1 Script Synthesizer

Reads a script with two characters and synthesizes it using
Microsoft MAI-Voice-1 voices via Azure Speech Service.
"""

import argparse
import json
import os
import sys
import xml.sax.saxutils as saxutils
from pathlib import Path

import requests
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv()

# Available MAI-Voice-1 voices
VOICES = {
    "iris": "en-US-Iris:MAI-Voice-1",
    "grant": "en-US-Grant:MAI-Voice-1",
    "jasper": "en-US-Jasper:MAI-Voice-1",
    "june": "en-US-June:MAI-Voice-1",
}

# Default voice assignments for the two characters
DEFAULT_VOICE_A = "iris"
DEFAULT_VOICE_B = "grant"


def build_ssml(lines: list[dict], voice_a: str, voice_b: str) -> str:
    """Build SSML from parsed script lines.

    Each line dict has: character, text, and optionally style.
    """
    voice_map = {
        "A": VOICES[voice_a],
        "B": VOICES[voice_b],
    }

    parts = [
        '<speak version="1.0" '
        'xmlns="http://www.w3.org/2001/10/synthesis" '
        'xmlns:mstts="https://www.w3.org/2001/mstts" '
        'xml:lang="en-US">'
    ]

    for line in lines:
        character = line["character"]
        text = saxutils.escape(line["text"])
        voice_name = voice_map[character]
        style = line.get("style")

        if style:
            parts.append(
                f'  <voice name="{voice_name}">'
                f'<mstts:express-as style="{style}">'
                f"{text}"
                f"</mstts:express-as></voice>"
            )
        else:
            parts.append(f'  <voice name="{voice_name}">{text}</voice>')

    parts.append("</speak>")
    return "\n".join(parts)


def parse_script(script_path: str) -> list[dict]:
    """Parse a script file into structured lines.

    Supported formats:
    - .json: List of {character, text, style?} objects
    - .txt:  Lines formatted as  CHARACTER: text
             Or CHARACTER (style): text
             Blank lines are skipped. CHARACTER must be A or B.
    """
    path = Path(script_path)

    if path.suffix == ".json":
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    lines = []
    with open(path, encoding="utf-8") as f:
        for raw in f:
            raw = raw.strip()
            if not raw or raw.startswith("#"):
                continue

            if ":" not in raw:
                print(f"Skipping malformed line: {raw}", file=sys.stderr)
                continue

            prefix, text = raw.split(":", 1)
            text = text.strip()
            prefix = prefix.strip()

            # Check for style in parentheses: A (excited): Hello!
            style = None
            if "(" in prefix and prefix.endswith(")"):
                char_part, style = prefix.split("(", 1)
                prefix = char_part.strip()
                style = style.rstrip(")").strip()

            character = prefix.upper()
            if character not in ("A", "B"):
                print(
                    f"Unknown character '{character}', must be A or B. Skipping.",
                    file=sys.stderr,
                )
                continue

            entry = {"character": character, "text": text}
            if style:
                entry["style"] = style
            lines.append(entry)

    return lines


def synthesize(
    script_path: str,
    output_path: str,
    voice_a: str = DEFAULT_VOICE_A,
    voice_b: str = DEFAULT_VOICE_B,
) -> None:
    """Synthesize a two-voice script to an audio file."""
    speech_key = os.getenv("SPEECH_KEY", "")
    speech_region = os.getenv("SPEECH_REGION", "eastus")
    speech_endpoint = os.getenv("SPEECH_ENDPOINT", "")

    lines = parse_script(script_path)
    if not lines:
        print("Error: No valid lines found in script.", file=sys.stderr)
        sys.exit(1)

    ssml = build_ssml(lines, voice_a, voice_b)

    # Print the SSML for debugging
    print("--- Generated SSML ---")
    print(ssml)
    print("----------------------\n")

    # Ensure output directory exists
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    # Build auth header
    if speech_key and speech_key != "your-azure-speech-key-here":
        headers = {"Ocp-Apim-Subscription-Key": speech_key}
        tts_url = f"https://{speech_region}.tts.speech.microsoft.com/cognitiveservices/v1"
    elif speech_endpoint:
        resource_name = speech_endpoint.replace("https://", "").split(".")[0]
        credential = DefaultAzureCredential()
        token = credential.get_token("https://cognitiveservices.azure.com/.default")
        headers = {"Authorization": f"Bearer {token.token}"}
        tts_url = f"{speech_endpoint}/tts/cognitiveservices/v1"
    else:
        print(
            "Error: Set SPEECH_KEY or SPEECH_ENDPOINT in .env.\n"
            "  Key auth:   SPEECH_KEY=<your-key>\n"
            "  Token auth: SPEECH_ENDPOINT=https://<name>.cognitiveservices.azure.com",
            file=sys.stderr,
        )
        sys.exit(1)

    headers["Content-Type"] = "application/ssml+xml"
    headers["X-Microsoft-OutputFormat"] = "riff-48khz-16bit-mono-pcm"
    headers["User-Agent"] = "MAI-Voice-Synthesizer"

    print(f"Synthesizing with voices: A={VOICES[voice_a]}, B={VOICES[voice_b]}")
    print(f"Script lines: {len(lines)}")
    print(f"Output: {out.resolve()}\n")

    response = requests.post(
        tts_url,
        headers=headers,
        data=ssml.encode("utf-8"),
        timeout=120,
    )

    if response.status_code == 200:
        out.write_bytes(response.content)
        print(f"Audio saved to {out.resolve()} ({len(response.content):,} bytes)")
    else:
        print(
            f"Synthesis failed: HTTP {response.status_code}",
            file=sys.stderr,
        )
        print(f"Response: {response.text[:500]}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Synthesize a two-voice script using MAI-Voice-1"
    )
    parser.add_argument("script", help="Path to script file (.txt or .json)")
    parser.add_argument(
        "-o",
        "--output",
        default="output/script.wav",
        help="Output audio file path (default: output/script.wav)",
    )
    parser.add_argument(
        "-a",
        "--voice-a",
        choices=list(VOICES.keys()),
        default=DEFAULT_VOICE_A,
        help=f"Voice for character A (default: {DEFAULT_VOICE_A})",
    )
    parser.add_argument(
        "-b",
        "--voice-b",
        choices=list(VOICES.keys()),
        default=DEFAULT_VOICE_B,
        help=f"Voice for character B (default: {DEFAULT_VOICE_B})",
    )
    parser.add_argument(
        "--ssml-only",
        action="store_true",
        help="Only print the generated SSML, don't synthesize",
    )

    args = parser.parse_args()

    if args.ssml_only:
        lines = parse_script(args.script)
        ssml = build_ssml(lines, args.voice_a, args.voice_b)
        print(ssml)
        return

    synthesize(args.script, args.output, args.voice_a, args.voice_b)


if __name__ == "__main__":
    main()
