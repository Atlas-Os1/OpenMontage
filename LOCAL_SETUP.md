# Local Setup (Colt's machine)

This is the local, non-upstream configuration for this OpenMontage install. Both
**Cowork-Claude** and **Cleo** (hermes agent) drive this same checkout.

## Install

- **Location:** `C:\Users\Minte\Desktop\Editor\OpenMontage`
- **Fork:** `github.com/Atlas-Os1/OpenMontage` — remotes: `origin` (fork),
  `upstream` (`calesthio/OpenMontage`).
- **Python:** system `python` 3.10, deps installed globally (so `python -c ...`
  works for any agent without activating a venv).
- **Node:** v22; `remotion-composer/node_modules` installed; HyperFrames via npx.
- **Runtimes:** FFmpeg, Remotion, HyperFrames all available (preflight passes).

Setup was done manually (no `make` on Windows):
`pip install -r requirements.txt`, `cd remotion-composer && npx --yes npm install`,
`pip install piper-tts`, `.env` from `.env.example`.

## Providers wired

- **Images:** `cloudflare_image` (Cloudflare Workers AI, FLUX) + stock
  (Pexels / Pixabay / Unsplash).
- **TTS:** Piper (free, offline).
- **Composition:** FFmpeg + Remotion + HyperFrames.
- No paid AI-video key yet — motion comes from Remotion/HyperFrames or the
  documentary-montage (real stock footage) pipeline.

## Cloudflare Workers AI

Custom provider `tools/graphics/cloudflare_image.py`. Routes through the deployed
OpenAI-compatible Worker (`cloudflare-worker/`, live at
`https://openmontage-ai.srvcflo.workers.dev`) when `CLOUDFLARE_AI_PROXY_URL` is
set; falls back to Workers AI REST otherwise. See `cloudflare-worker/README.md`.

## Secrets

- `.env` (gitignored) holds all keys — already populated.
- Plaintext reference: `C:\Users\Minte\Desktop\Editor\Editor keys.txt`.
- Never commit `.env` or the keys file; never echo full token values.

## Cleo (hermes) integration

Cleo has matching skills under `C:\Users\Minte\AppData\Local\hermes\skills\media\`:
`openmontage` (this system), plus video skills `reel-studio`, `reels-scripting`,
`youtube-thumbnail`, `gemini-infographic`, `quote-post`.

## Agent contract

Read `AGENT_GUIDE.md` first (Rule Zero: all production goes through a pipeline),
then `PROJECT_CONTEXT.md`, then pipeline manifest + stage director skills. Run the
preflight (`registry.provider_menu_summary()`) before proposing work.
