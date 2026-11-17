"""Orchestrator stub — run pipeline stages for one episode.

Usage (once implemented):
  python -m pipeline.run episodes/2026-01-example-slug
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import ai_video, assemble, elevenlabs, script, youtube


STAGES = ("script", "elevenlabs", "ai_video", "assemble", "youtube")


def run_episode(episode_dir: Path, *, from_stage: str = "script") -> None:
    """Run stages in order starting at from_stage.

    v0: validates paths / loads VO; later stages raise NotImplementedError
    until APIs and ffmpeg are wired.
    """
    if from_stage not in STAGES:
        raise SystemExit(f"Unknown stage {from_stage!r}; choose from {STAGES}")

    paths = script.EpisodePaths.from_episode_dir(episode_dir)
    start = STAGES.index(from_stage)

    if start <= STAGES.index("script"):
        if not paths.script.exists():
            raise FileNotFoundError(paths.script)
        vo = script.load_vo_block(paths.script)
        print(f"[script] loaded VO ({len(vo)} chars) from {paths.script}")

    if start <= STAGES.index("elevenlabs"):
        # TODO: pass VO text into synthesize
        out = paths.root / "voice.mp3"
        print(f"[elevenlabs] would synthesize → {out} (voice={elevenlabs.voice_id()})")
        elevenlabs.synthesize("(VO placeholder — load from script)", out)

    if start <= STAGES.index("ai_video"):
        clips = paths.root / "clips"
        print(f"[ai_video] would generate clips → {clips}")
        # TODO: parse shot list from script-short.md
        ai_video.generate_all([], clips)

    if start <= STAGES.index("assemble"):
        print(f"[assemble] would build short.mp4 under {paths.root}")
        assemble.assemble(paths.root)

    if start <= STAGES.index("youtube"):
        print(f"[youtube] would upload from {paths.root}")
        youtube.upload(paths.root)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Car Anatomy Shorts pipeline (stub)")
    parser.add_argument("episode", type=Path, help="Path to episodes/YYYY-NN-slug")
    parser.add_argument(
        "--from",
        dest="from_stage",
        default="script",
        choices=STAGES,
        help="Start at this stage (default: script)",
    )
    args = parser.parse_args(argv)
    try:
        run_episode(args.episode, from_stage=args.from_stage)
    except NotImplementedError as exc:
        print(f"stub: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
