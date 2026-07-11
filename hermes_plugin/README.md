# OpenMontage Hermes provider plugin

This is the first integration slice for OpenMontage and Hermes.

It provides these tools:

- `openmontage_provider_inventory` — returns the provider/model routing catalog.
- `openmontage_provider_status` — reports credential presence by environment-variable name only.
- `openmontage_model_route` — recommends available models by media department, quality, and lane.
- `openmontage_generate_image` — calls Cloudflare `/ai/run`, writes the image, hashes it, and records R2 metadata.
- `openmontage_generate_voice` — delegates to OpenMontage's ElevenLabs tool, writes narration, hashes it, and records R2 metadata.
- `openmontage_generate_video` — delegates ranking/generation to OpenMontage's existing VideoSelector and provider fallbacks.

## Install into another Hermes profile

From the OpenMontage checkout:

```bash
python scripts/install_hermes_plugin.py \\
  --hermes-home /opt/data/profiles/Atlas-Content/.hermes
hermes plugins enable openmontage
```

For atlas-content, run the installer in the atlas-content/OpenMontage checkout
or copy this repository to the profile workspace first. The installer copies
only `hermes_plugin/`; it does not copy `.env`, credentials, generated media,
or R2 files. Restart the atlas-content Hermes process after enabling the plugin.

## Transport boundary

The plugin distinguishes Cloudflare Workers AI (`@cf/...`) from Cloudflare AI
Gateway partner models (`google/...`, `bytedance/...`, `pruna/...`, and
`runwayml/...`). Image execution currently uses Cloudflare's universal
`/ai/run` route. Video execution delegates to OpenMontage's existing
`VideoSelector`; its live provider path still depends on the configured
provider (FAL, Replicate, Runway, HeyGen, or an available local model).

- Workers AI `@cf/...` models are discoverable through the account Workers AI catalog and use Workers AI model-specific schemas.
- Partner models use the Cloudflare AI Gateway `/ai/run` envelope and their own model-specific input schemas. Do not use the Workers AI `/ai/models/schema` result as proof that a partner route is unavailable.
- A model listed in the routing catalog is a candidate, not a successful smoke test. The execution layer must verify the model and payload before paid generation.
- Secret values remain in the owning Hermes/profile `.env`; never commit `.env` files or API keys.
