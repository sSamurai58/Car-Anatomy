"""Assemble stage tests (ffmpeg presence + dry helpers)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from pipeline import assemble


def test_require_ffmpeg_missing() -> None:
    with patch("shutil.which", return_value=None):
        with pytest.raises(RuntimeError, match="ffmpeg not found"):
            assemble.require_ffmpeg()


def test_write_timeline(tmp_path: Path) -> None:
    clips_dir = tmp_path / "clips"
    clips_dir.mkdir()
    c1 = clips_dir / "01.mp4"
    c2 = clips_dir / "02.mp4"
    c1.write_bytes(b"x")
    c2.write_bytes(b"y")
    voice = tmp_path / "voice.mp3"
    voice.write_bytes(b"a")
    timeline = tmp_path / "timeline.json"
    assemble.write_timeline(timeline, clips=[c1, c2], audio=voice)
    data = assemble.load_timeline(timeline)
    assert data["aspect"] == "9:16"
    assert data["clips"][0]["path"] == "clips/01.mp4"
    assert data["audio"] == "voice.mp3"
