---
name: openmontage-provider-routing
description: Route OpenMontage media work through Cloudflare, OpenAI, NVIDIA, stock sources, and ElevenLabs without exposing credentials.
---

# OpenMontage provider routing

Use `openmontage_provider_status` before selecting a provider. Treat environment-variable presence as configuration evidence only; a real provider smoke test is required before claiming a model works.

## Department defaults

- Images: Cloudflare AI Gateway partner models first when catalog-verified; Workers AI FLUX models for fast drafts and reliable fallback.
- Image understanding: `@cf/moondream/moondream3.1-9B-A2B` when available.
- Video generation: Cloudflare AI Gateway partner models such as Seedance, Pruna P-Video, or Runway Aleph only after live catalog and endpoint verification.
- Voice: ElevenLabs for production voice; Cloudflare Aura or MeloTTS for low-cost fallback.
- Stock media: Pexels, Pixabay, Unsplash, and archive sources according to the OpenMontage source policy.
- Text and small auxiliary tasks: Cloudflare hosted models or NVIDIA backup routing, depending on live availability and cost.
- Rendering: OpenMontage Remotion, HyperFrames, and FFmpeg remain local/runtime capabilities, not hosted model calls.

## Hard rules

1. Never print secret values.
2. Never assume a model name is available because it appears in a stale config file.
3. Separate Workers AI `@cf/...` models from AI Gateway partner models.
4. Announce provider, model, transport, and whether a call is draft or batch before paid generation.
5. Verify generated artifacts independently before publishing to R2 or minte.dev.
