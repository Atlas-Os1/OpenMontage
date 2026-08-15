# SlidesAdapter

Layer 2 skill for the `SlidesAdapter` tool (`tools/presentation/slides_adapter.py`).

## Purpose

Convert canonical OpenMontage artifacts into Workspace Slides JSON so humans can review, edit, and export decks before or after video production.

## Actions

### `scene_plan_to_deck`

Input: `scene_plan`, optional `title`, `project`, and `placeholders` (`scene_id -> image_url`). Output: a Workspace Slides-compatible deck with an orange cover and one scene slide per scene.

Use after `scene_plan` approval and before `assets` generation. It is a cheap review checkpoint that prevents expensive re-renders.

### `key_moments_to_deck`

Input: `key_moments` (`timestamp`, `caption`, optional `title` and `image_url`), optional `title`, `project`, and `render_path`. Output: a shareable summary deck.

Use after `compose`/`publish`; sample frames with `frame_sampler` and pass image URLs and accurate captions.

### `create_title_slide` / `create_content_slide`

Low-level helpers for custom decks.

### `save_deck` / `load_deck`

Persist or read deck JSON. Preferred path: `projects/<project>/artifacts/<artifact_name>.json`.

## Quality rules

- Always include an orange cover slide and the brand bottom bar on content slides.
- Keep titles concise (≤80 characters) and captions readable at 19px.
- Use placeholders only when they faithfully represent the scene intent; omit misleading placeholders.
- Decks must declare `themeVersion: "workspace.1"`.
