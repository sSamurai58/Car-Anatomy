"""ffmpeg assemble stage — stub.

Build a 9:16 master short.mp4 from voice.mp3 + clips/ (+ optional captions).
Timeline input: episodes/.../timeline.json (schema TBD).
"""

from __future__ import annotations

import json
from pathlib import Path


def load_timeline(timeline_path: Path) -> dict:
    """Load JSON timeline describing clip order, cuts, and overlays.

    TODO: define stable schema (clips[], audio, captions, duration).
    """
    return json.loads(Path(timeline_path).read_text(encoding="utf-8"))


def assemble(
    episode_dir: Path,
    *,
    voice_path: Path | None = None,
    clips_dir: Path | None = None,
    timeline_path: Path | None = None,
    out_path: Path | None = None,
) -> Path:
    """Assemble the Short master.

    TODO:
    - Default paths under episode_dir (voice.mp3, clips/, timeline.json, short.mp4)
    - Invoke ffmpeg (concat / filter_complex) for 9:16
    - Burn or soft-mux captions from script on-screen text
    - Normalize loudness for YouTube Shorts
    """
    root = Path(episode_dir)
    voice_path = voice_path or root / "voice.mp3"
    clips_dir = clips_dir or root / "clips"
    timeline_path = timeline_path or root / "timeline.json"
    out_path = out_path or root / "short.mp4"
    _ = (voice_path, clips_dir, timeline_path)
    raise NotImplementedError(
        "ffmpeg assemble not wired yet — see TODOs in pipeline/assemble.py"
    )
