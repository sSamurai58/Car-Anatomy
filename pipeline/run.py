"""Orchestrator — run pipeline stages for one episode.

Usage:
  python -m pipeline.run episodes/2026-01-example-slug
  python -m pipeline.run episodes/2026-01-example-slug --dry-run
  python -m pipeline.run episodes/2026-01-example-slug --from assemble
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import ai_video, assemble, elevenlabs, script, youtube


STAGES = ("script", "elevenlabs", "ai_video", "assemble", "youtube")


def _load_dotenv(path: Path) -> None:
    """Minimal .env loader (no dependency). Does not override existing env."""
    import os

    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


def run_episode(
    episode_dir: Path,
    *,
    from_stage: str = "script",
    dry_run: bool = False,
    skip_youtube: bool = False,
) -> None:
    """Run stages in order starting at from_stage.

    dry_run: parse script / print plan; skip paid ElevenLabs + Kling calls
    (and therefore assemble/youtube unless media already exists and you start later).
    """
    if from_stage not in STAGES:
        raise SystemExit(f"Unknown stage {from_stage!r}; choose from {STAGES}")

    paths = script.EpisodePaths.from_episode_dir(episode_dir)
    if not paths.root.exists():
        raise FileNotFoundError(paths.root)

    start = STAGES.index(from_stage)
    parsed: script.ParsedScript | None = None
    voice_out = paths.root / "voice.mp3"
    clips_dir = paths.root / "clips"
    timeline_path = paths.root / "timeline.json"

    if start <= STAGES.index("script"):
        if not paths.script.exists():
            raise FileNotFoundError(paths.script)
        parsed = script.parse_script(paths.script)
        print(
            f"[script] VO={len(parsed.vo)} chars, shots={len(parsed.shots)}, "
            f"captions={len(parsed.captions)} ← {paths.script}"
        )
        for shot in parsed.shots:
            print(
                f"  shot {shot.index:02d} {shot.start_s:g}-{shot.end_s:g}s "
                f"({ai_video.kling_duration_for_shot(shot)}s Kling): "
                f"{shot.prompt[:80]}"
            )

    if start <= STAGES.index("elevenlabs"):
        if parsed is None:
            parsed = script.parse_script(paths.script)
        print(f"[elevenlabs] voice={elevenlabs.voice_id()} → {voice_out}")
        if dry_run:
            print("[elevenlabs] dry-run: skipping paid TTS API")
        else:
            elevenlabs.synthesize(parsed.vo, voice_out)
            print(f"[elevenlabs] wrote {voice_out} ({voice_out.stat().st_size} bytes)")

    if start <= STAGES.index("ai_video"):
        if parsed is None:
            parsed = script.parse_script(paths.script)
        print(
            f"[ai_video] provider={ai_video.provider_name()} "
            f"mode={ai_video.api_mode()} → {clips_dir}"
        )
        if dry_run:
            print(f"[ai_video] dry-run: would generate {len(parsed.shots)} Kling clip(s)")
        else:
            clip_paths = ai_video.generate_all(parsed.shots, clips_dir)
            assemble.write_timeline(
                timeline_path,
                clips=clip_paths,
                audio=voice_out,
            )
            print(f"[ai_video] wrote {len(clip_paths)} clip(s); timeline → {timeline_path}")

    if start <= STAGES.index("assemble"):
        if dry_run and not (clips_dir.exists() and any(clips_dir.glob("*.mp4"))):
            print("[assemble] dry-run: no local clips — skipping ffmpeg")
        elif dry_run and not voice_out.exists():
            print("[assemble] dry-run: no voice.mp3 — skipping ffmpeg")
        else:
            print(f"[assemble] building short.mp4 under {paths.root}")
            out = assemble.assemble(
                paths.root,
                voice_path=voice_out,
                clips_dir=clips_dir,
                timeline_path=timeline_path,
            )
            print(f"[assemble] wrote {out} ({out.stat().st_size} bytes)")

    if start <= STAGES.index("youtube"):
        if dry_run or skip_youtube:
            reason = "dry-run" if dry_run else "--skip-youtube"
            print(f"[youtube] {reason}: skipping upload")
            return
        print(f"[youtube] uploading from {paths.root}")
        video_id = youtube.upload(paths.root)
        print(f"[youtube] uploaded id={video_id}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Car Anatomy Shorts pipeline")
    parser.add_argument("episode", type=Path, help="Path to episodes/YYYY-NN-slug")
    parser.add_argument(
        "--from",
        dest="from_stage",
        default="script",
        choices=STAGES,
        help="Start at this stage (default: script)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse script and print plan; skip paid ElevenLabs/Kling (and YouTube)",
    )
    parser.add_argument(
        "--skip-youtube",
        action="store_true",
        help="Stop after assemble (default for local renders)",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=Path(".env"),
        help="Optional dotenv path (default: ./.env); never commit secrets",
    )
    args = parser.parse_args(argv)
    _load_dotenv(args.env_file)
    try:
        run_episode(
            args.episode,
            from_stage=args.from_stage,
            dry_run=args.dry_run,
            skip_youtube=args.skip_youtube,
        )
    except NotImplementedError as exc:
        print(f"not implemented: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
