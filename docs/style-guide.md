# Car Anatomy — style guide

## Brand

- **Name:** Car Anatomy (hero-level brand signal on thumbs/end cards; not just a watermark)
- **Promise:** Make one car system make sense in under a minute
- **Voice:** Confident engineer-explainer — short sentences, concrete nouns, no hype adjectives without a fact behind them

## Short structure (~45–60s)

| Beat | Time | Job |
|---|---|---|
| Hook | 0–2s | Visual + spoken punch; name the system or surprise |
| Setup | ~5–10s | What people think / what the car is doing |
| Mechanism | ~25–35s | One clear cause → effect; 1–3 facts max |
| Takeaway | ~5–8s | One line the viewer can repeat |
| End | ~2–3s | Brand / “next Short” cue — no hard sell |

## Language (EN-US)

- US spelling and terms (hood, transmission, gas, not petrol)
- Prefer model names viewers know (Mustang, Corvette, Camaro, Porsche 911, etc.) when they illustrate a system
- Banned: empty clickbait (“You won’t believe…”), unverifiable claims, dealer-speak, ranking listicles

## On-screen text

- Max ~6–8 words per caption beat
- High contrast; safe margins for Shorts UI
- Captions follow VO; do not invent extra claims on screen

## Visuals (AI video)

- Vertical **9:16** only
- One shot = one visual idea from the shot list
- Prefer cutaway / diagram / motion that shows the mechanism over beauty B-roll alone
- Provider: **Kling** (`pipeline/ai_video.py`) — keep prompts mechanism-first; 9:16

## Audio

- ElevenLabs voice `TX3LPaxmHKxFdv7VOQHJ`
- VO drives pace; leave ~0.2–0.4s breath between major beats
- Music: low under VO if used; never mask consonants

## Thumbnail / cover

- Brand name readable at phone size
- One subject + one short title fragment
- No crowded badge stacks or fake UI chrome

## Episode folder naming

`episodes/YYYY-NN-slug/` e.g. `episodes/2026-01-mustang-v8-sound/`
