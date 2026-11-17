"""Unit tests for script parsing (no paid APIs)."""

from __future__ import annotations

from pathlib import Path

from pipeline.script import load_shots, load_vo_block, parse_script


SAMPLE = """# Script — demo

**Full VO (paste for TTS):**

```
A Mustang V8 doesn't roar by accident — it's exhaust pulses stacking up.
```

---

## Shot list

| # | t (s) | Visual / prompt gist | Notes |
|---|------:|----------------------|-------|
| 1 | 0–2 | Extreme close-up of Mustang dual exhaust tips pulsing | Hook |
| 2 | 2–10 | Cutaway of V8 firing order, 9:16 | Setup |
| 3 | 10–45 | Exhaust pulse waves merging in the pipe | Mechanism |

---

## On-screen captions

| t (s) | Text (≤8 words) |
|------:|-----------------|
| 0–2 | Exhaust pulses |
| 45–55 | One idea: pulse timing |

---

## End screen

- Brand: **Car Anatomy**
"""


def test_load_vo_and_shots(tmp_path: Path) -> None:
    script_path = tmp_path / "script-short.md"
    script_path.write_text(SAMPLE, encoding="utf-8")

    vo = load_vo_block(script_path)
    assert "Mustang V8" in vo

    shots = load_shots(script_path)
    assert len(shots) == 3
    assert shots[0].index == 1
    assert shots[0].start_s == 0.0
    assert shots[0].end_s == 2.0
    assert "exhaust tips" in shots[0].prompt.lower()
    assert shots[2].end_s == 45.0

    parsed = parse_script(script_path)
    assert len(parsed.captions) == 2
