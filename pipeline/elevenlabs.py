"""ElevenLabs TTS stage.

Locked voice_id: TX3LPaxmHKxFdv7VOQHJ (override via ELEVENLABS_VOICE_ID).
Requires ELEVENLABS_API_KEY in the environment. Never hardcode secrets.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_VOICE_ID = "TX3LPaxmHKxFdv7VOQHJ"
DEFAULT_MODEL_ID = "eleven_multilingual_v2"
DEFAULT_OUTPUT_FORMAT = "mp3_44100_128"
API_BASE = "https://api.elevenlabs.io/v1"


def voice_id() -> str:
    return os.environ.get("ELEVENLABS_VOICE_ID", DEFAULT_VOICE_ID)


def model_id() -> str:
    return os.environ.get("ELEVENLABS_MODEL_ID", DEFAULT_MODEL_ID)


def _api_key() -> str:
    key = (os.environ.get("ELEVENLABS_API_KEY") or "").strip()
    if not key:
        raise RuntimeError(
            "ELEVENLABS_API_KEY is not set. Copy secrets.example.env → .env and fill it in."
        )
    return key


def synthesize(text: str, out_path: Path) -> Path:
    """Write narration audio to out_path (e.g. episodes/.../voice.mp3)."""
    cleaned = (text or "").strip()
    if not cleaned:
        raise ValueError("TTS text is empty")

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    vid = voice_id()
    url = (
        f"{API_BASE}/text-to-speech/{vid}"
        f"?output_format={DEFAULT_OUTPUT_FORMAT}"
    )
    body = {
        "text": cleaned,
        "model_id": model_id(),
        "voice_settings": {
            # Slightly higher stability for Shorts pacing / clarity.
            "stability": 0.45,
            "similarity_boost": 0.75,
            "style": 0.15,
            "use_speaker_boost": True,
        },
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": _api_key(),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            audio = resp.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"ElevenLabs TTS failed ({exc.code}): {detail}") from exc

    if not audio:
        raise RuntimeError("ElevenLabs returned empty audio")

    out.write_bytes(audio)
    return out
