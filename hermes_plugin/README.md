# OpenMontage Hermes provider plugin

This is the first integration slice for OpenMontage and Hermes.

It provides these tools:

- `openmontage_provider_inventory` — returns the provider/model routing catalog.
- `openmontage_provider_status` — reports credential presence by environment-variable name only.
- `openmontage_model_route` — recommends available models by media department, quality, and lane.
- `openmontage_tool_catalog` — exposes the complete OpenMontage registry (86 tools, 18 capabilities) with declared input schemas without importing optional ML dependencies.
- `openmontage_execute_tool` — executes any existing OpenMontage `BaseTool` by catalog name.
- `openmontage_preflight_edit` — checks engine, FFmpeg/FFprobe, paths, Layer 2/3 skills, manifests, and schemas.
- `openmontage_pipeline_catalog` — lists instruction-driven pipeline manifests.
- `openmontage_pipeline_manifest` — returns stage order, director skills, required tools, review focus, and approval extensions.
- `openmontage_artifact_schema` — returns canonical artifact JSON schemas.
- `openmontage_validate_checkpoint` — validates checkpoint and canonical artifact payloads.
- `openmontage_generate_image` — calls Cloudflare `/ai/run`, writes the image, hashes it, and records R2 metadata.
- `openmontage_generate_voice` — delegates to OpenMontage's ElevenLabs tool, writes narration, hashes it, and records R2 metadata.
- `openmontage_generate_video` — delegates ranking/generation to OpenMontage's existing VideoSelector and provider fallbacks.

The generic registry bridge covers real editing capabilities including source ingest,
clip retrieval, analysis, transcription, captions, audio processing, graphics,
enhancement, character animation, video generation, video composition, transitions,
reframing, stitching, trimming, rendering, and visual QA.

## OpenMontage architecture

The plugin respects the project's three-layer model:

1. **Layer 1 — tools:** the engine checkout and `tools/tool_registry.py` remain the runtime source of truth.
2. **Layer 2 — OpenMontage skills:** pipeline/stage director instructions in `skills/` teach the agent how to use the tools.
3. **Layer 3 — technology skills:** `.agents/skills/` supplies generic API and framework knowledge.

The agent drives pipeline state and approvals. The plugin does not introduce a Python
orchestration layer or replace the project's canonical artifacts/checkpoint protocol.

## Install into another Hermes profile

From the OpenMontage checkout:

```bash
python scripts/install_hermes_plugin.py \\
  --hermes-home /opt/data/profiles/atlas-content
hermes --profile atlas-content plugins enable openmontage
```

The installer copies the Hermes plugin into `<hermes-home>/plugins/openmontage`,
the OpenMontage Layer 3 technology skill pack into `<hermes-home>/skills/openmontage`,
and the Layer 2 pipeline/director skill pack into
`<hermes-home>/skills/openmontage-core`. It writes an engine-root marker so the
registry bridge can find the checkout. It does not copy `.env`, credentials,
generated media, or R2 files. Restart the target Hermes process after enabling
the plugin.

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
