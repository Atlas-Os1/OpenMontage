# Publish-Deck Director — Explainer Pipeline

## When to Use

Run after `publish` has produced a `render_report` (and optionally a `publish_log`). Build a lightweight, shareable key-moments deck from the finished video.

## Input Artifacts

- `render_report` (required): final video path, duration, and output profile.
- `publish_log` (optional): chapter markers, SEO title, and description.
- `edit_decisions` (optional): subtitle or narration text for captions.

## Output Artifact

`key_moments_deck`, saved at `projects/<project>/artifacts/key_moments_deck.json`.

## Process

1. Select moments from chapter markers, narrative cuts, or even sampling every 8–15 seconds (or 20–25% of duration).
2. Derive one accurate, concise sentence per moment from subtitles, script narration, or publish metadata.
3. Use `frame_sampler` to extract frames under `projects/<project>/assets/frames/`.
4. Call `SlidesAdapter` with `action: key_moments_to_deck`, then persist with `action: save_deck`.

## Review Focus

Key moments cover the full video at meaningful narrative points; captions match the video; image URLs reference rendered frames; moments are chronological. Use 3–5 moments for short videos.

## Success Criteria

- `projects/<project>/artifacts/key_moments_deck.json` exists.
- The deck is schema-valid and contains at least one moment slide.
- The user can optionally open it in Workspace Slides and export to PDF.
