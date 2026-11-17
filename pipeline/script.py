"""Script stage — load brief + Short script from an episode folder.

No LLM calls here in v0; agents author Markdown from templates.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class EpisodePaths:
    root: Path
    brief: Path
    script: Path
    meta: Path

    @classmethod
    def from_episode_dir(cls, episode_dir: Path) -> "EpisodePaths":
        root = Path(episode_dir)
        return cls(
            root=root,
            brief=root / "brief.md",
            script=root / "script-short.md",
            meta=root / "meta.json",
        )


def load_vo_block(script_path: Path) -> str:
    """Extract the fenced 'Full VO' block from script-short.md.

    TODO: harden parser (frontmatter, multiple fences).
    """
    text = Path(script_path).read_text(encoding="utf-8")
    marker = "**Full VO (paste for TTS):**"
    if marker not in text:
        raise ValueError(f"VO block marker not found in {script_path}")
    after = text.split(marker, 1)[1]
    if "```" not in after:
        raise ValueError(f"VO fenced block missing in {script_path}")
    body = after.split("```", 2)[1]
    return body.strip()


def ensure_episode_scaffold(episode_dir: Path, templates_dir: Path | None = None) -> EpisodePaths:
    """Copy templates into a new episode folder if missing.

    TODO: wire CLI `pipeline new-episode YYYY-NN-slug`.
    """
    paths = EpisodePaths.from_episode_dir(episode_dir)
    paths.root.mkdir(parents=True, exist_ok=True)
    # TODO: copy from templates/ when templates_dir is provided
    _ = templates_dir
    return paths
