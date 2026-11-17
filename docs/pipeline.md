# Pipeline setup — ElevenLabs + Kling

End-to-end Shorts render (local):

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp secrets.example.env .env   # fill keys; never commit .env
# require ffmpeg on PATH
python -m pipeline.run episodes/YYYY-NN-slug --skip-youtube
```

Dry-run (no paid APIs):

```bash
python -m pipeline.run episodes/YYYY-NN-slug --dry-run
```

## Stages

| Stage | Module | Paid? | Notes |
|---|---|---|---|
| Script | `pipeline/script.py` | No | Parses VO + shot list from `script-short.md` |
| TTS | `pipeline/elevenlabs.py` | Yes | `ELEVENLABS_API_KEY` + voice `TX3LPaxmHKxFdv7VOQHJ` |
| Clips | `pipeline/ai_video.py` | Yes | Kling text-to-video, 9:16 |
| Assemble | `pipeline/assemble.py` | No | ffmpeg → `short.mp4` |
| Upload | `pipeline/youtube.py` | — | Still stub |

## ElevenLabs

- Env: `ELEVENLABS_API_KEY` (required), `ELEVENLABS_VOICE_ID` (default locked voice)
- Writes `episodes/.../voice.mp3`
- Cursor Secrets: set `ELEVENLABS_API_KEY` (already verified for this project)

## Kling

Official docs: [Authentication](https://kling.ai/document-api/api/get-started/authentication), [Kling 2.6 Text to Video](https://kling.ai/document-api/api/video/2-6/text-to-video).

**Add one of these to Cursor Secrets:**

1. **Preferred:** `KLING_API_KEY` — single Bearer API key from the Kling console  
2. **Legacy JWT:** `KLING_ACCESS_KEY` **and** `KLING_SECRET_KEY` — client signs HS256 JWT (`iss`=access key, `exp`≈30m)

Aliases accepted: `KLINGAI_API_KEY`, `KLINGAI_ACCESS_KEY`, `KLINGAI_SECRET_KEY`.

| Env | Purpose |
|---|---|
| `KLING_API_KEY` | Current official auth |
| `KLING_ACCESS_KEY` + `KLING_SECRET_KEY` | Legacy JWT auth |
| `KLING_API_BASE` | Default `https://api-singapore.klingai.com` |
| `KLING_API_MODE` | `path` (default, `/text-to-video/kling-2.6`) or `legacy` (`/v1/videos/text2video`) |
| `AI_VIDEO_PROVIDER` | Must be `kling` (default) |

### Assumptions

- Default create path: `POST /text-to-video/kling-2.6` with `settings.aspect_ratio=9:16`, duration `5` or `10` (mapped from shot timing).
- Poll: `GET /tasks?task_ids=...` until `succeeded` / `failed` (also accepts legacy `succeed`).
- If only AK/SK are set (no API key), the client auto-selects **legacy** mode (`/v1/videos/text2video` + JWT), which matches older console credentials.
- Clip URLs are temporary; downloaded immediately into `clips/NN.mp4`.
- CI / `--dry-run` never call Kling or ElevenLabs.

## ffmpeg

Required for assemble. Clear error if missing. Output is 1080×1920 H.264 + AAC VO (`-shortest`).
