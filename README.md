# Car Anatomy

Automated **YouTube Shorts** pipeline for the **Car Anatomy** channel: how cars work, focused on US cars and sportscars.

Each Short is ~45–60 seconds, vertical 9:16, English (US). One idea per video — hook → mechanism → takeaway.

## Pipeline (v0)

```
Topic
  → brief (templates/brief.md)
  → script (templates/script-short.md)
  → voice.mp3        (pipeline/elevenlabs)
  → clips/           (pipeline/ai_video — provider TBD)
  → short.mp4        (pipeline/assemble via ffmpeg)
  → thumbnail.png
  → meta.json
  → YouTube upload   (pipeline/youtube — trial private, then auto)
```

| Stage | Module | Status |
|---|---|---|
| Script / brief | Agent + templates | Ready to author |
| TTS | `pipeline/elevenlabs.py` | Stub — needs `ELEVENLABS_API_KEY` |
| AI video | `pipeline/ai_video.py` | Stub — provider TBD |
| Assemble | `pipeline/assemble.py` | Stub — ffmpeg + JSON timeline |
| Upload | `pipeline/youtube.py` | Stub — YouTube Data API v3 |

Run stages via `python -m pipeline.run` once modules are wired (see `pipeline/`).

## Repo layout

```
docs/           Channel positioning + style guide
templates/      Brief, Short script, meta, thumbnail notes
episodes/       Per-Short working folders (YYYY-NN-slug/)
assets/brand/   Logos, fonts, color refs
pipeline/       Thin stubs: script → TTS → AI video → ffmpeg → YouTube
secrets.example.env
```

## Secrets

Copy `secrets.example.env` → local `.env` (never commit). Required later:

- `ELEVENLABS_API_KEY`
- `ELEVENLABS_VOICE_ID` (default: `TX3LPaxmHKxFdv7VOQHJ`)
- `YOUTUBE_*` OAuth / Data API credentials

## Content pillars

1. Powertrains  
2. Drivetrain  
3. Chassis & brakes  
4. Electronics  
5. Icons & anatomy (one model, one system)

**Out of scope (v1):** long-form, dealer reviews, Top-10 listicles, news fluff.

## Publish policy

First **N ≈ 5** Shorts upload as **private/unlisted** for review, then switch to auto-public.
