"""Orchestrator dry-run does not call paid APIs."""

from __future__ import annotations

from pathlib import Path

from pipeline.run import run_episode


SAMPLE = """# Script — dry

**Full VO (paste for TTS):**

```
Limited-slip diffs send torque to the wheel that can use it.
```

## Shot list

| # | t (s) | Visual / prompt gist | Notes |
|---|------:|----------------------|-------|
| 1 | 0–5 | Corvette rear differential cutaway, vertical 9:16 | Hook |
"""


def test_dry_run_skips_paid(tmp_path: Path, capsys) -> None:
    ep = tmp_path / "2026-01-dry"
    ep.mkdir()
    (ep / "script-short.md").write_text(SAMPLE, encoding="utf-8")
    run_episode(ep, dry_run=True, skip_youtube=True)
    out = capsys.readouterr().out
    assert "dry-run: skipping paid TTS" in out
    assert "dry-run: would generate 1 Kling" in out
    assert not (ep / "voice.mp3").exists()
