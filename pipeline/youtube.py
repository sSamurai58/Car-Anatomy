"""YouTube Data API upload stage — stub.

Trial policy: first N uploads as private/unlisted, then auto-public.
Never commit OAuth secrets; use env vars from secrets.example.env.
"""

from __future__ import annotations

import json
import os
from pathlib import Path


def default_privacy() -> str:
    return os.environ.get("YOUTUBE_DEFAULT_PRIVACY", "private")


def load_meta(meta_path: Path) -> dict:
    return json.loads(Path(meta_path).read_text(encoding="utf-8"))


def upload(episode_dir: Path, *, privacy: str | None = None) -> str:
    """Upload short.mp4 + metadata (+ optional thumbnail).

    Returns YouTube video id when implemented.

    TODO:
    - OAuth with YOUTUBE_CLIENT_ID / YOUTUBE_CLIENT_SECRET / YOUTUBE_REFRESH_TOKEN
    - videos.insert with snippet + status.privacyStatus
    - thumbnails.set when thumbnail.png exists
    - Enforce trial private/unlisted until N approved
    """
    root = Path(episode_dir)
    meta = load_meta(root / "meta.json")
    privacy = privacy or meta.get("privacyStatus") or default_privacy()
    video_path = root / meta.get("videoPath", "short.mp4")
    thumb = root / meta.get("thumbnailPath", "thumbnail.png")
    _ = (
        video_path,
        thumb,
        privacy,
        os.environ.get("YOUTUBE_CLIENT_ID"),
        os.environ.get("YOUTUBE_CLIENT_SECRET"),
        os.environ.get("YOUTUBE_REFRESH_TOKEN"),
        os.environ.get("YOUTUBE_CHANNEL_ID"),
    )
    raise NotImplementedError(
        "YouTube upload not wired yet — see TODOs in pipeline/youtube.py"
    )
