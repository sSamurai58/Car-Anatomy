"""Kling auth resolution tests (mocked; no network)."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from pipeline import ai_video


@pytest.fixture(autouse=True)
def _clear_kling_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in list(os.environ):
        if key.startswith("KLING") or key.startswith("KLINGAI") or key == "AI_VIDEO_PROVIDER":
            monkeypatch.delenv(key, raising=False)


def test_api_key_preferred(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KLING_API_KEY", "key-from-api")
    monkeypatch.setenv("KLING_ACCESS_KEY", "ak")
    monkeypatch.setenv("KLING_SECRET_KEY", "sk")
    assert ai_video.auth_bearer() == "key-from-api"
    assert ai_video.api_mode() == "path"


def test_jwt_from_access_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("jwt")
    monkeypatch.setenv("KLING_ACCESS_KEY", "test-ak")
    monkeypatch.setenv("KLING_SECRET_KEY", "test-sk-at-least-32-bytes-long!!")
    token = ai_video.auth_bearer()
    assert isinstance(token, str) and token.count(".") == 2
    assert ai_video.api_mode() == "legacy"


def test_missing_credentials_raises() -> None:
    with pytest.raises(RuntimeError, match="Kling credentials missing"):
        ai_video.auth_bearer()


def test_kling_duration_mapping() -> None:
    short = ai_video.Shot(1, 0, 5, "p")
    long = ai_video.Shot(2, 0, 12, "p")
    assert ai_video.kling_duration_for_shot(short) == 5
    assert ai_video.kling_duration_for_shot(long) == 10


def test_create_task_path_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KLING_API_KEY", "k")
    monkeypatch.setenv("KLING_API_MODE", "path")

    def fake_request(method, url, body=None, timeout=60.0):
        assert method == "POST"
        assert url.endswith("/text-to-video/kling-2.6")
        assert body["settings"]["aspect_ratio"] == "9:16"
        return {"code": 0, "data": {"id": "task-123", "status": "submitted"}}

    with patch.object(ai_video, "_request_json", side_effect=fake_request):
        task_id = ai_video.create_text2video_task("A Corvette LSD at work", duration=5)
    assert task_id == "task-123"
