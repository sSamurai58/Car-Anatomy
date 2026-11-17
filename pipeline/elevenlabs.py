"""ElevenLabs TTS stage — stub.

Locked voice_id: TX3LPaxmHKxFdv7VOQHJ (override via ELEVENLABS_VOICE_ID).
Do not call the API until ELEVENLABS_API_KEY is set in the environment.
"""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_VOICE_ID = "TX3LPaxmHKxFdv7VOQHJ"


def voice_id() -> str:
    return os.environ.get("ELEVENLABS_VOICE_ID", DEFAULT_VOICE_ID)


def synthesize(text: str, out_path: Path) -> Path:
    """Write narration audio to out_path (e.g. episodes/.../voice.mp3).

    TODO:
    - Call ElevenLabs text-to-speech with voice_id()
    - Read ELEVENLABS_API_KEY from env (never hardcode)
    - Choose model/stability settings for Shorts pacing
    - Raise a clear error if the API key is missing
    """
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ELEVENLABS_API_KEY is not set. Copy secrets.example.env → .env and fill it in."
        )
    _ = (text, voice_id(), out_path)
    raise NotImplementedError("ElevenLabs TTS not wired yet — see TODOs in pipeline/elevenlabs.py")
