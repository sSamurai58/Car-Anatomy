# Car Anatomy

Automated **YouTube Shorts** pipeline for the **Car Anatomy** channel: how cars work, focused on US cars and sportscars.

Each Short is ~45–60 seconds, vertical 9:16, English (US). One idea per video — hook → mechanism → takeaway.

## Pipeline

```
Topic
  → brief (templates/brief.md)
  → script (templates/script-short.md)
  → voice.mp3        (pipeline/elevenlabs — ElevenLabs TTS)
  → clips/           (pipeline/ai_video — Kling text-to-video)
  → short.mp4        (pipeline/assemble via ffmpeg)
  → thumbnail.png
  → meta.json
  → YouTube upload   (pipeline/youtube — still stub; trial private, then auto)
```

| Stage | Module | Status |
|---|---|---|
| Script / brief | Agent + templates | Parses VO + shot list |
| TTS | `pipeline/elevenlabs.py` | Wired — needs `ELEVENLABS_API_KEY` |
| AI video | `pipeline/ai_video.py` | Wired — **Kling** (`KLING_API_KEY` or AK/SK) |
| Assemble | `pipeline/assemble.py` | Wired — requires `ffmpeg` |
| Upload | `pipeline/youtube.py` | Stub — YouTube Data API v3 |

```bash
pip install -r requirements.txt
cp secrets.example.env .env   # fill keys locally; never commit
python -m pipeline.run episodes/YYYY-NN-slug --dry-run
python -m pipeline.run episodes/YYYY-NN-slug --skip-youtube
```

See [docs/pipeline.md](docs/pipeline.md) for Kling + ElevenLabs setup details.

## Repo layout

```
docs/           Channel positioning, style guide, pipeline setup
templates/      Brief, Short script, meta, thumbnail notes
episodes/       Per-Short working folders (YYYY-NN-slug/)
assets/brand/   Logos, fonts, color refs
pipeline/       script → ElevenLabs → Kling → ffmpeg → YouTube
secrets.example.env
requirements.txt
```

## Secrets

Copy `secrets.example.env` → local `.env` (never commit). For Cursor Secrets / local:

| Variable | Required for | Notes |
|---|---|---|
| `ELEVENLABS_API_KEY` | TTS | Already used successfully for this channel |
| `ELEVENLABS_VOICE_ID` | TTS | Default `TX3LPaxmHKxFdv7VOQHJ` |
| `KLING_API_KEY` | Clips | **Preferred** Kling Bearer API key |
| `KLING_ACCESS_KEY` + `KLING_SECRET_KEY` | Clips | Legacy JWT pair if no API key |
| `YOUTUBE_*` | Upload | OAuth / Data API (stub stage) |

Do **not** call paid Kling/ElevenLabs from CI. Use `--dry-run` or unit tests with mocks.

## Content pillars

1. Powertrains  
2. Drivetrain  
3. Chassis & brakes  
4. Electronics  
5. Icons & anatomy (one model, one system)

**Out of scope (v1):** long-form, dealer reviews, Top-10 listicles, news fluff.

## Publish policy

First **N ≈ 5** Shorts upload as **private/unlisted** for review, then switch to auto-public.
