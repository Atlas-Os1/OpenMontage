# OpenMontage AI Worker (Cloudflare Workers AI proxy)

OpenAI-compatible proxy over Cloudflare Workers AI. Gives OpenMontage (and any
OpenAI-style client) image generation — and basic chat — backed by your Workers
AI plan, with no per-image paid third-party key.

- **Live URL:** https://openmontage-ai.srvcflo.workers.dev
- **Account:** `ff3c5e2beaea9f85fee3200bfe28da16` (Serviceflowagi@gmail.com)
- **Binding:** `AI` (Workers AI) — see `wrangler.toml`

## Endpoints

| Method | Path | Notes |
|--------|------|-------|
| GET  | `/` | health check |
| GET  | `/v1/models` | list mapped model ids |
| POST | `/v1/images/generations` | OpenAI-style → `{ data: [{ b64_json }] }` |
| POST | `/v1/chat/completions` | OpenAI-style → Workers AI LLM |

Image models: `flux-schnell` (default), `sdxl`, `sdxl-lightning`, `dreamshaper`.
Chat models: `llama-3.1-8b` (default), `llama-3.3-70b`.

## How OpenMontage uses it

`tools/graphics/cloudflare_image.py` (provider `cloudflare`, capability
`image_generation`) prefers this proxy when `CLOUDFLARE_AI_PROXY_URL` is set in
`.env`, otherwise calls Workers AI REST directly.

## Optional auth

```bash
npx wrangler secret put PROXY_SECRET     # then set CLOUDFLARE_AI_PROXY_SECRET in .env
```

## Redeploy / add models

The account's API token (`CLOUDFLARE_WORKERS_R2_TOKEN`) can't reach wrangler's
newer `workers/services` route, so deploy via the classic Workers Scripts API:

```bash
# from cloudflare-worker/
ACCT=ff3c5e2beaea9f85fee3200bfe28da16
TOK=<CLOUDFLARE_WORKERS_R2_TOKEN>
curl -X PUT "https://api.cloudflare.com/client/v4/accounts/$ACCT/workers/scripts/openmontage-ai" \
  -H "Authorization: Bearer $TOK" \
  -F "metadata=@metadata.json;type=application/json" \
  -F "worker.js=@src/worker.js;type=application/javascript+module"
```

To use `npx wrangler deploy` instead, create an API token with **Workers
Scripts: Edit** permission and set it as `CLOUDFLARE_API_TOKEN`.

Add new image/video models by editing `IMAGE_MODELS` / `CHAT_MODELS` in
`src/worker.js`, then re-run the curl upload above.
