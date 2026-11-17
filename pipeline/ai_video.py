"""AI video generation stage — stub.

Provider is TBD (Runway / Kling / Veo / other). Keep prompts in the episode
shot list; this module should stay provider-swappable.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Shot:
    index: int
    start_s: float
    end_s: float
    prompt: str
    notes: str = ""


def provider_name() -> str | None:
    return os.environ.get("AI_VIDEO_PROVIDER")


def generate_clip(shot: Shot, out_path: Path) -> Path:
    """Generate one vertical 9:16 clip for a shot.

    TODO:
    - Select provider from AI_VIDEO_PROVIDER
    - Call provider API with shot.prompt (9:16)
    - Write clip to out_path (e.g. clips/01.mp4)
    - No fake HTTP calls; implement when provider is locked
    """
    _ = (shot, out_path, provider_name(), os.environ.get("AI_VIDEO_API_KEY"))
    raise NotImplementedError(
        "AI video provider not chosen yet — see TODOs in pipeline/ai_video.py"
    )


def generate_all(shots: list[Shot], clips_dir: Path) -> list[Path]:
    """Generate every shot into clips_dir / NN.mp4.

    TODO: parallelize carefully; respect provider rate limits.
    """
    clips_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for shot in shots:
        out = clips_dir / f"{shot.index:02d}.mp4"
        paths.append(generate_clip(shot, out))
    return paths
