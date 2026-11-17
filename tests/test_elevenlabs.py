"""ElevenLabs client tests (mocked HTTP)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pipeline import elevenlabs


def test_synthesize_writes_mp3(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-key")
    out = tmp_path / "voice.mp3"

    fake_resp = MagicMock()
    fake_resp.read.return_value = b"ID3fake-mp3"
    fake_resp.__enter__.return_value = fake_resp
    fake_resp.__exit__.return_value = False

    with patch("urllib.request.urlopen", return_value=fake_resp) as mocked:
        path = elevenlabs.synthesize("Hello from Car Anatomy.", out)

    assert path == out
    assert out.read_bytes() == b"ID3fake-mp3"
    mocked.assert_called_once()
    req = mocked.call_args[0][0]
    assert "text-to-speech" in req.full_url
    # urllib Request normalizes header names; accept either form.
    headers = {k.lower(): v for k, v in req.header_items()}
    assert headers.get("xi-api-key") == "test-key"


def test_missing_api_key(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="ELEVENLABS_API_KEY"):
        elevenlabs.synthesize("hi", tmp_path / "v.mp3")
