"""ffmpeg assemble stage.

Build a 9:16 master short.mp4 from voice.mp3 + clips/ (+ optional timeline.json).
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

TARGET_W = 1080
TARGET_H = 1920


def require_ffmpeg() -> str:
    path = shutil.which("ffmpeg")
    if not path:
        raise RuntimeError(
            "ffmpeg not found on PATH. Install ffmpeg "
            "(e.g. `apt install ffmpeg` / `brew install ffmpeg`) and retry."
        )
    return path


def load_timeline(timeline_path: Path) -> dict[str, Any]:
    """Load JSON timeline describing clip order, cuts, and overlays."""
    return json.loads(Path(timeline_path).read_text(encoding="utf-8"))


def write_timeline(
    timeline_path: Path,
    *,
    clips: list[Path],
    audio: Path,
    width: int = TARGET_W,
    height: int = TARGET_H,
) -> Path:
    # Prefer episode-relative paths for readability.
    clip_entries = []
    for c in clips:
        rel = f"clips/{c.name}" if c.parent.name == "clips" else str(c)
        clip_entries.append({"path": rel})
    payload = {
        "aspect": "9:16",
        "width": width,
        "height": height,
        "audio": audio.name if audio.parent == Path(timeline_path).parent else str(audio),
        "clips": clip_entries,
    }
    Path(timeline_path).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return Path(timeline_path)


def _resolve_clip_paths(episode_dir: Path, timeline: dict[str, Any], clips_dir: Path) -> list[Path]:
    entries = timeline.get("clips") or []
    paths: list[Path] = []
    for entry in entries:
        if isinstance(entry, str):
            raw = entry
        elif isinstance(entry, dict):
            raw = entry.get("path") or entry.get("source") or ""
        else:
            continue
        p = Path(raw)
        if not p.is_absolute():
            candidate = episode_dir / p
            if not candidate.exists():
                candidate = clips_dir / p.name
            p = candidate
        paths.append(p)
    if paths:
        return paths
    # Fall back to sorted clips/*.mp4
    return sorted(clips_dir.glob("*.mp4"))


def assemble(
    episode_dir: Path,
    *,
    voice_path: Path | None = None,
    clips_dir: Path | None = None,
    timeline_path: Path | None = None,
    out_path: Path | None = None,
) -> Path:
    """Assemble the Short master (9:16) with ffmpeg."""
    ffmpeg = require_ffmpeg()
    root = Path(episode_dir)
    voice_path = Path(voice_path or root / "voice.mp3")
    clips_dir = Path(clips_dir or root / "clips")
    timeline_path = Path(timeline_path or root / "timeline.json")
    out_path = Path(out_path or root / "short.mp4")

    if not voice_path.exists():
        raise FileNotFoundError(f"Missing voice track: {voice_path}")

    timeline: dict[str, Any]
    if timeline_path.exists():
        timeline = load_timeline(timeline_path)
    else:
        discovered = sorted(clips_dir.glob("*.mp4"))
        if not discovered:
            raise FileNotFoundError(
                f"No clips found in {clips_dir} and no timeline at {timeline_path}"
            )
        write_timeline(timeline_path, clips=discovered, audio=voice_path)
        timeline = load_timeline(timeline_path)

    clip_paths = _resolve_clip_paths(root, timeline, clips_dir)
    missing = [str(p) for p in clip_paths if not p.exists()]
    if missing:
        raise FileNotFoundError(f"Timeline clips missing: {missing}")
    if not clip_paths:
        raise FileNotFoundError(f"No clips to assemble under {clips_dir}")

    width = int(timeline.get("width") or TARGET_W)
    height = int(timeline.get("height") or TARGET_H)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Scale/pad each clip to 9:16, concat, then mux VO (shortest = VO length).
    with tempfile.TemporaryDirectory(prefix="car-anatomy-assemble-") as tmp:
        tmp_dir = Path(tmp)
        normalized: list[Path] = []
        vf = (
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,"
            f"setsar=1,fps=30,format=yuv420p"
        )
        for i, clip in enumerate(clip_paths):
            norm = tmp_dir / f"norm_{i:02d}.mp4"
            cmd = [
                ffmpeg,
                "-y",
                "-i",
                str(clip),
                "-an",
                "-vf",
                vf,
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "20",
                str(norm),
            ]
            _run(cmd, label=f"normalize clip {clip.name}")
            normalized.append(norm)

        concat_list = tmp_dir / "concat.txt"
        concat_list.write_text(
            "".join(f"file '{p.as_posix()}'\n" for p in normalized),
            encoding="utf-8",
        )
        silent_video = tmp_dir / "video_silent.mp4"
        _run(
            [
                ffmpeg,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_list),
                "-c",
                "copy",
                str(silent_video),
            ],
            label="concat clips",
        )

        # Map VO as sole audio; trim/pad to shortest stream for Shorts length.
        _run(
            [
                ffmpeg,
                "-y",
                "-i",
                str(silent_video),
                "-i",
                str(voice_path),
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-shortest",
                "-movflags",
                "+faststart",
                str(out_path),
            ],
            label="mux voice",
        )

    return out_path


def _run(cmd: list[str], *, label: str) -> None:
    try:
        subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "ffmpeg not found on PATH. Install ffmpeg and retry."
        ) from exc
    except subprocess.CalledProcessError as exc:
        err = (exc.stderr or exc.stdout or "").strip()[-1200:]
        raise RuntimeError(f"ffmpeg failed during {label}: {err}") from exc
