"""Script stage — load brief + Short script from an episode folder.

No LLM calls here in v0; agents author Markdown from templates.
Parses VO + shot list from templates/script-short.md structure.
"""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from .ai_video import Shot


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


@dataclass
class ParsedScript:
    vo: str
    shots: list[Shot]
    captions: list[tuple[str, str]]


_TIME_RANGE = re.compile(
    r"^\s*(\d+(?:\.\d+)?)\s*[–—-]\s*(\d+(?:\.\d+)?)\s*$"
)


def _parse_time_range(cell: str) -> tuple[float, float] | None:
    text = (cell or "").strip()
    if not text or text.startswith("<!--"):
        return None
    match = _TIME_RANGE.match(text)
    if not match:
        return None
    return float(match.group(1)), float(match.group(2))


def _split_table_row(line: str) -> list[str] | None:
    stripped = line.strip()
    if not stripped.startswith("|"):
        return None
    # Drop leading/trailing empty cells from outer pipes.
    cells = [c.strip() for c in stripped.strip("|").split("|")]
    return cells


def _is_separator_row(cells: list[str]) -> bool:
    if not cells:
        return True
    return all(re.fullmatch(r":?-{3,}:?", c.replace(" ", "")) for c in cells if c)


def load_vo_block(script_path: Path) -> str:
    """Extract the fenced 'Full VO' block from script-short.md."""
    text = Path(script_path).read_text(encoding="utf-8")
    marker = "**Full VO (paste for TTS):**"
    if marker not in text:
        raise ValueError(f"VO block marker not found in {script_path}")
    after = text.split(marker, 1)[1]
    if "```" not in after:
        raise ValueError(f"VO fenced block missing in {script_path}")
    body = after.split("```", 2)[1]
    vo = body.strip()
    # Ignore HTML comment placeholders left from the template.
    if not vo or vo.startswith("<!--"):
        raise ValueError(
            f"VO block in {script_path} is empty or still a template placeholder"
        )
    return vo


def load_shots(script_path: Path) -> list[Shot]:
    """Parse the ## Shot list markdown table into Shot objects."""
    text = Path(script_path).read_text(encoding="utf-8")
    if "## Shot list" not in text:
        raise ValueError(f"## Shot list section not found in {script_path}")

    after = text.split("## Shot list", 1)[1]
    # Stop at next H2 if present.
    section = after.split("\n## ", 1)[0]
    shots: list[Shot] = []
    for line in section.splitlines():
        cells = _split_table_row(line)
        if cells is None or len(cells) < 3:
            continue
        if cells[0].lower() in {"#", "no", "n"}:
            continue
        if _is_separator_row(cells):
            continue
        index_raw, time_raw, prompt = cells[0], cells[1], cells[2]
        notes = cells[3] if len(cells) > 3 else ""
        if not index_raw.isdigit():
            continue
        times = _parse_time_range(time_raw)
        if times is None:
            # Allow blank time cells — fall back to sequential 5s windows.
            start_s = float(len(shots) * 5)
            end_s = start_s + 5.0
        else:
            start_s, end_s = times
        prompt_clean = prompt.strip()
        if not prompt_clean or prompt_clean.startswith("<!--"):
            continue
        shots.append(
            Shot(
                index=int(index_raw),
                start_s=start_s,
                end_s=end_s,
                prompt=prompt_clean,
                notes=notes.strip(),
            )
        )

    if not shots:
        raise ValueError(f"No filled shot rows found in {script_path}")
    return shots


def load_captions(script_path: Path) -> list[tuple[str, str]]:
    """Parse ## On-screen captions table → list of (time, text)."""
    text = Path(script_path).read_text(encoding="utf-8")
    if "## On-screen captions" not in text:
        return []
    after = text.split("## On-screen captions", 1)[1]
    section = after.split("\n## ", 1)[0]
    captions: list[tuple[str, str]] = []
    for line in section.splitlines():
        cells = _split_table_row(line)
        if cells is None or len(cells) < 2:
            continue
        if cells[0].lower().startswith("t") and "s" in cells[0].lower():
            continue
        if _is_separator_row(cells):
            continue
        t_cell, text_cell = cells[0].strip(), cells[1].strip()
        if not text_cell or text_cell.startswith("<!--"):
            continue
        captions.append((t_cell, text_cell))
    return captions


def parse_script(script_path: Path) -> ParsedScript:
    path = Path(script_path)
    return ParsedScript(
        vo=load_vo_block(path),
        shots=load_shots(path),
        captions=load_captions(path),
    )


def ensure_episode_scaffold(episode_dir: Path, templates_dir: Path | None = None) -> EpisodePaths:
    """Copy templates into a new episode folder if missing."""
    paths = EpisodePaths.from_episode_dir(episode_dir)
    paths.root.mkdir(parents=True, exist_ok=True)
    root = Path(__file__).resolve().parents[1]
    templates = Path(templates_dir) if templates_dir else root / "templates"
    mapping = {
        paths.brief: templates / "brief.md",
        paths.script: templates / "script-short.md",
        paths.meta: templates / "meta.json",
    }
    for dest, src in mapping.items():
        if dest.exists() or not src.exists():
            continue
        shutil.copyfile(src, dest)
    return paths
