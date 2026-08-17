# Storyboard Director — Explainer Pipeline

## When to Use

Run immediately after the approved `scene_plan` and before `assets`. Turn the approved plan into a human-reviewable slide deck so stakeholders can sign off before asset-generation cost is incurred.

## Input Artifacts

- `scene_plan` (required): scenes, timings, narration, and required assets.
- `proposal_packet` (optional): project title, selected concept, and style playbook.

## Output Artifact

`scene_plan_deck`, saved at `projects/<project>/artifacts/scene_plan_deck.json`.

## Process

1. Choose `proposal_packet.selected_concept.title`, then `scene_plan.project`/`scene_plan.title`, otherwise `Storyboard`.
2. Optionally generate one faithful placeholder key frame per scene with `image_selector`; log each decision and skip placeholders if unavailable or costly.
3. Call `SlidesAdapter` with `action: scene_plan_to_deck`, then persist with `action: save_deck`.
4. Present one slide per scene in scene order and ask for approval, revision, or abort. Regenerate after requested revisions before proceeding to assets.

## Review Focus

Every scene shows timing, narration, visual summary, and any faithful placeholder. Slide order matches `scene_plan`; JSON is valid Workspace Slides JSON.

## Success Criteria

- `projects/<project>/artifacts/scene_plan_deck.json` exists.
- The deck is schema-valid with one scene slide per scene.
- Explicit human approval is recorded before assets begins.

## Common Pitfalls

Do not omit this checkpoint. Do not over-produce placeholders. A static placeholder cannot prove motion-led scenes work; flag those scenes for extra review.
