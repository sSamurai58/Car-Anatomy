"""AI video generation via Kling (Kuaishou).

Provider locked to Kling. Auth (see secrets.example.env / docs/pipeline.md):

Preferred (current official API Key auth):
  KLING_API_KEY   (alias: KLINGAI_API_KEY)

Legacy JWT (Access Key + Secret Key → HS256 Bearer token):
  KLING_ACCESS_KEY + KLING_SECRET_KEY
  (aliases: KLINGAI_ACCESS_KEY + KLINGAI_SECRET_KEY)

API modes:
  - default / "path": POST /text-to-video/kling-2.6 + GET /tasks?task_ids=
    (current docs; model in path; prefers API key)
  - "legacy": POST /v1/videos/text2video + GET /v1/videos/text2video/{id}
    (model_name body field; JWT-friendly)

Override base URL with KLING_API_BASE (default https://api-singapore.klingai.com).
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_BASE = "https://api-singapore.klingai.com"
DEFAULT_MODEL_PATH = "kling-2.6"
DEFAULT_LEGACY_MODEL = "kling-v2-6"
DEFAULT_ASPECT = "9:16"
DEFAULT_MODE = "std"
DEFAULT_POLL_INTERVAL = 8.0
DEFAULT_POLL_TIMEOUT = 600.0


@dataclass
class Shot:
    index: int
    start_s: float
    end_s: float
    prompt: str
    notes: str = ""

    @property
    def duration_s(self) -> float:
        return max(0.0, self.end_s - self.start_s)


def provider_name() -> str:
    return os.environ.get("AI_VIDEO_PROVIDER", "kling").strip().lower() or "kling"


def api_base() -> str:
    return (os.environ.get("KLING_API_BASE") or DEFAULT_BASE).rstrip("/")


def api_mode() -> str:
    """Return 'path' (new) or 'legacy'."""
    explicit = (os.environ.get("KLING_API_MODE") or "").strip().lower()
    if explicit in {"path", "legacy", "new"}:
        return "legacy" if explicit == "legacy" else "path"
    # Prefer legacy endpoint when only access/secret keys are present.
    if _api_key_raw() is None and _access_secret() is not None:
        return "legacy"
    return "path"


def _env_first(*names: str) -> str | None:
    for name in names:
        value = (os.environ.get(name) or "").strip()
        if value:
            return value
    return None


def _api_key_raw() -> str | None:
    return _env_first("KLING_API_KEY", "KLINGAI_API_KEY")


def _access_secret() -> tuple[str, str] | None:
    ak = _env_first("KLING_ACCESS_KEY", "KLINGAI_ACCESS_KEY")
    sk = _env_first("KLING_SECRET_KEY", "KLINGAI_SECRET_KEY")
    if ak and sk:
        return ak, sk
    if ak or sk:
        raise RuntimeError(
            "Kling JWT auth requires both KLING_ACCESS_KEY and KLING_SECRET_KEY "
            "(or KLINGAI_ACCESS_KEY + KLINGAI_SECRET_KEY)."
        )
    return None


def _encode_jwt(ak: str, sk: str) -> str:
    """HS256 JWT per Kling docs (iss=ak, exp=+30m, nbf=-5s)."""
    try:
        import jwt  # PyJWT
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "PyJWT is required for KLING_ACCESS_KEY/KLING_SECRET_KEY auth. "
            "Install deps from requirements.txt."
        ) from exc

    now = int(time.time())
    payload = {"iss": ak, "exp": now + 1800, "nbf": now - 5}
    headers = {"alg": "HS256", "typ": "JWT"}
    token = jwt.encode(payload, sk, algorithm="HS256", headers=headers)
    return token if isinstance(token, str) else token.decode("utf-8")


def auth_bearer() -> str:
    """Resolve Authorization bearer token (never log the value)."""
    api_key = _api_key_raw()
    if api_key:
        return api_key
    pair = _access_secret()
    if pair:
        return _encode_jwt(*pair)
    raise RuntimeError(
        "Kling credentials missing. Set KLING_API_KEY (preferred), or "
        "KLING_ACCESS_KEY + KLING_SECRET_KEY. See secrets.example.env."
    )


def kling_duration_for_shot(shot: Shot) -> int:
    """Kling text2video accepts 5 or 10 second clips."""
    dur = shot.duration_s
    if dur <= 0:
        return 5
    return 10 if dur > 7.5 else 5


def _request_json(
    method: str,
    url: str,
    *,
    body: dict[str, Any] | None = None,
    timeout: float = 60.0,
) -> dict[str, Any]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {auth_bearer()}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:800]
        raise RuntimeError(f"Kling HTTP {exc.code} for {method} {url}: {detail}") from exc

    if not raw.strip():
        return {}
    payload = json.loads(raw)
    if isinstance(payload, dict) and payload.get("code") not in (None, 0, "0"):
        raise RuntimeError(
            f"Kling API error code={payload.get('code')}: {payload.get('message')}"
        )
    return payload if isinstance(payload, dict) else {"data": payload}


def create_text2video_task(
    prompt: str,
    *,
    duration: int = 5,
    aspect_ratio: str = DEFAULT_ASPECT,
    negative_prompt: str = "",
) -> str:
    """Create a Kling text-to-video task; return task id."""
    cleaned = (prompt or "").strip()
    if not cleaned:
        raise ValueError("Kling prompt is empty")
    if duration not in (5, 10):
        duration = 5

    mode = api_mode()
    base = api_base()

    if mode == "legacy":
        body: dict[str, Any] = {
            "model_name": os.environ.get("KLING_MODEL_NAME", DEFAULT_LEGACY_MODEL),
            "prompt": cleaned,
            "duration": str(duration),
            "mode": os.environ.get("KLING_MODE", DEFAULT_MODE),
            "aspect_ratio": aspect_ratio,
        }
        if negative_prompt.strip():
            body["negative_prompt"] = negative_prompt.strip()
        payload = _request_json("POST", f"{base}/v1/videos/text2video", body=body)
        data = payload.get("data") or {}
        task_id = data.get("task_id") or data.get("id")
    else:
        model_path = os.environ.get("KLING_TEXT2VIDEO_MODEL", DEFAULT_MODEL_PATH).lstrip("/")
        body = {
            "prompt": cleaned,
            "settings": {
                "aspect_ratio": aspect_ratio,
                "duration": duration,
                "resolution": os.environ.get("KLING_RESOLUTION", "720p"),
                "audio": os.environ.get("KLING_NATIVE_AUDIO", "off"),
            },
            "options": {
                "watermark_info": {"enabled": False},
            },
        }
        if negative_prompt.strip():
            # New path docs fold negatives into prompt; keep optional legacy field if set.
            body["prompt"] = f"{cleaned}. Avoid: {negative_prompt.strip()}"
        payload = _request_json("POST", f"{base}/text-to-video/{model_path}", body=body)
        data = payload.get("data") or {}
        task_id = data.get("id") or data.get("task_id")

    if not task_id:
        raise RuntimeError(f"Kling create response missing task id: {payload}")
    return str(task_id)


def _normalize_status(status: str | None) -> str:
    s = (status or "").strip().lower()
    if s in {"succeed", "succeeded", "success"}:
        return "succeeded"
    if s in {"fail", "failed", "error"}:
        return "failed"
    return s


def _video_url_from_task(data: dict[str, Any]) -> str | None:
    outputs = data.get("outputs")
    if isinstance(outputs, list):
        for item in outputs:
            if not isinstance(item, dict):
                continue
            if item.get("type") in (None, "video") and item.get("url"):
                return str(item["url"])
    result = data.get("task_result") or {}
    videos = result.get("videos") if isinstance(result, dict) else None
    if isinstance(videos, list) and videos:
        first = videos[0]
        if isinstance(first, dict) and first.get("url"):
            return str(first["url"])
    return None


def get_task(task_id: str) -> dict[str, Any]:
    """Fetch a single Kling task payload (normalized dict)."""
    mode = api_mode()
    base = api_base()
    if mode == "legacy":
        payload = _request_json("GET", f"{base}/v1/videos/text2video/{urllib.parse.quote(task_id)}")
        data = payload.get("data") or {}
        if isinstance(data, list):
            data = data[0] if data else {}
        return data if isinstance(data, dict) else {}

    qs = urllib.parse.urlencode({"task_ids": task_id})
    payload = _request_json("GET", f"{base}/tasks?{qs}")
    data = payload.get("data")
    if isinstance(data, list):
        if not data:
            return {}
        item = data[0]
        return item if isinstance(item, dict) else {}
    return data if isinstance(data, dict) else {}


def poll_task(
    task_id: str,
    *,
    interval_s: float | None = None,
    timeout_s: float | None = None,
) -> dict[str, Any]:
    """Poll until succeeded/failed; return final task dict."""
    interval = interval_s or float(os.environ.get("KLING_POLL_INTERVAL", DEFAULT_POLL_INTERVAL))
    timeout = timeout_s or float(os.environ.get("KLING_POLL_TIMEOUT", DEFAULT_POLL_TIMEOUT))
    started = time.monotonic()
    last: dict[str, Any] = {}

    while True:
        last = get_task(task_id)
        status = _normalize_status(str(last.get("status") or last.get("task_status") or ""))
        if status == "succeeded":
            return last
        if status == "failed":
            msg = last.get("message") or last.get("task_status_msg") or "unknown"
            raise RuntimeError(f"Kling task {task_id} failed: {msg}")
        if time.monotonic() - started > timeout:
            raise TimeoutError(f"Kling task {task_id} timed out after {timeout}s (last={status!r})")
        time.sleep(interval)


def download_url(url: str, out_path: Path) -> Path:
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": "car-anatomy-pipeline/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = resp.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"Failed to download Kling clip ({exc.code}): {detail}") from exc
    if not data:
        raise RuntimeError("Downloaded Kling clip was empty")
    out.write_bytes(data)
    return out


def generate_clip(shot: Shot, out_path: Path) -> Path:
    """Generate one vertical 9:16 clip for a shot via Kling."""
    if provider_name() not in {"kling", "klingai", "kuaishou"}:
        raise RuntimeError(
            f"Unsupported AI_VIDEO_PROVIDER={provider_name()!r}; this pipeline is Kling-only."
        )

    out = Path(out_path)
    if out.exists() and out.stat().st_size > 0:
        return out

    duration = kling_duration_for_shot(shot)
    task_id = create_text2video_task(shot.prompt, duration=duration, aspect_ratio=DEFAULT_ASPECT)
    print(f"[ai_video] shot {shot.index:02d} task={task_id} duration={duration}s")
    task = poll_task(task_id)
    url = _video_url_from_task(task)
    if not url:
        raise RuntimeError(f"Kling task {task_id} succeeded but no video URL: {task}")
    return download_url(url, out)


def generate_all(shots: list[Shot], clips_dir: Path) -> list[Path]:
    """Generate every shot into clips_dir / NN.mp4."""
    if not shots:
        raise ValueError("No shots to generate — parse the script shot list first")
    clips_dir = Path(clips_dir)
    clips_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for shot in shots:
        if not (shot.prompt or "").strip():
            raise ValueError(f"Shot {shot.index} has an empty visual prompt")
        out = clips_dir / f"{shot.index:02d}.mp4"
        paths.append(generate_clip(shot, out))
    return paths
