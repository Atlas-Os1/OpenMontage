"""Workspace Slides adapter for OpenMontage.

Converts canonical OpenMontage artifacts into slide decks that can be loaded
into the Workspace Slides gadget for human review, approval, and PDF export.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from tools.base_tool import (
    BaseTool,
    Determinism,
    ExecutionMode,
    ResourceProfile,
    ToolResult,
    ToolRuntime,
    ToolStability,
    ToolTier,
)


CANVAS_W = 1200
CANVAS_H = 675

_BRAND_RUBY = "#FF6633"
_BRAND_TANGERINE = "#F6821F"
_BRAND_MANGO = "#FBAD41"
_BRAND_BLACK = "#000000"
_BRAND_GRAY = "#747474"

_BOTTOM_BAR_SVG = (
    '<svg xmlns="@url:`http://www.w3.org/2000/svg`" viewBox="0 0 1200 12" '
    'preserveAspectRatio="none">'
    '<defs><linearGradient id="g">'
    '<stop stop-color="#FF6633"/>'
    '<stop offset=".5" stop-color="#F6821F"/>'
    '<stop offset="1" stop-color="#FBAD41"/>'
    "</linearGradient></defs>"
    '<rect width="1200" height="12" fill="url(#g)"/>'
    "</svg>"
)


def _gen_id() -> str:
    """Return a short random ID matching the Workspace Slides client style."""
    return uuid.uuid4().hex[:8]


def _bottom_bar() -> dict[str, Any]:
    return {
        "id": _gen_id(),
        "type": "svg",
        "x": 0,
        "y": 663,
        "w": CANVAS_W,
        "h": 12,
        "props": {"markup": _BOTTOM_BAR_SVG, "fit": "stretch", "background": ""},
    }


def make_title_slide(title: str, subtitle: str = "") -> dict[str, Any]:
    """Return an orange Workspace Slides cover slide."""
    slide: dict[str, Any] = {
        "id": _gen_id(),
        "background": {"color": _BRAND_TANGERINE, "inset": False, "coverOrange": True},
        "blocks": [
            {"id": _gen_id(), "type": "logo", "x": 36, "y": 56, "w": 267, "props": {}},
            {
                "id": _gen_id(), "type": "title", "x": 33, "y": 197, "w": 687,
                "props": {"text": title, "fontSize": 58, "weight": 700, "color": "#FFFFFF",
                          "letterSpacing": "-0.03em", "lineHeight": 1.1, "highlight": ""},
            },
        ],
    }
    if subtitle:
        slide["blocks"].append({
            "id": _gen_id(), "type": "subtitle", "x": 36, "y": 533, "w": 553,
            "props": {"text": subtitle, "fontSize": 17, "weight": 600, "color": "#FFFFFF", "lineHeight": 1.5},
        })
    return slide


def make_content_slide(eyebrow: str, headline: str, body: str) -> dict[str, Any]:
    """Return a standard white Workspace Slides content slide."""
    return {
        "id": _gen_id(), "background": {"color": "#FFFFFF", "inset": False, "dotGrid": 0},
        "blocks": [
            {"id": _gen_id(), "type": "sectionLabel", "x": 36, "y": 35, "props": {"text": eyebrow}},
            {"id": _gen_id(), "type": "title", "x": 35, "y": 76, "w": 984,
             "props": {"text": headline, "fontSize": 28, "weight": 600, "color": _BRAND_BLACK,
                       "letterSpacing": "-0.03em", "lineHeight": 1.2, "highlight": ""}},
            {"id": _gen_id(), "type": "logo", "x": 1013, "y": 40, "props": {"variant": "dark", "scale": 0.62}},
            {"id": _gen_id(), "type": "text", "x": 36, "y": 204, "w": 760,
             "props": {"text": body, "fontSize": 19, "weight": 400, "color": _BRAND_GRAY,
                       "family": "sans", "align": "left", "lineHeight": 1.6}},
            _bottom_bar(),
        ],
    }


def _standard_header(blocks: list[dict[str, Any]], eyebrow: str, title: str) -> None:
    blocks.extend([
        {"id": _gen_id(), "type": "sectionLabel", "x": 36, "y": 35, "props": {"text": eyebrow}},
        {"id": _gen_id(), "type": "title", "x": 35, "y": 76, "w": 984,
         "props": {"text": title, "fontSize": 28, "weight": 600, "color": _BRAND_BLACK,
                   "letterSpacing": "-0.03em", "lineHeight": 1.2, "highlight": ""}},
        {"id": _gen_id(), "type": "logo", "x": 1013, "y": 40, "props": {"variant": "dark", "scale": 0.62}},
    ])


def make_scene_slide(scene: dict[str, Any], idx: int, placeholder_url: str | None = None) -> dict[str, Any]:
    """Build one storyboard slide for a scene_plan scene."""
    start = float(scene.get("start_time", 0.0) or 0.0)
    duration = float(scene.get("duration", 0.0) or 0.0)
    end = start + duration
    visual_summary = (scene.get("description") or scene.get("visual") or scene.get("id") or "")[:80]
    narration = scene.get("narration", "") or scene.get("dialogue", "") or ""
    blocks: list[dict[str, Any]] = []
    _standard_header(blocks, f"SCENE {idx:02d}", visual_summary)
    blocks.extend([
        {"id": _gen_id(), "type": "text", "x": 36, "y": 150, "w": 550,
         "props": {"text": narration, "fontSize": 17, "weight": 400, "color": _BRAND_BLACK,
                   "family": "sans", "align": "left", "lineHeight": 1.5}},
        {"id": _gen_id(), "type": "text", "x": 36, "y": 620, "w": 550,
         "props": {"text": f"Time: {start:.1f}s – {end:.1f}s", "fontSize": 15, "weight": 600,
                   "color": _BRAND_RUBY, "family": "sans", "align": "left", "lineHeight": 1.4}},
    ])
    if placeholder_url:
        blocks.append({"id": _gen_id(), "type": "image", "x": 620, "y": 135, "w": 544, "h": 450,
                       "props": {"src": placeholder_url, "fit": "cover"}})
    blocks.append(_bottom_bar())
    return {"id": _gen_id(), "background": {"color": "#FFFFFF", "inset": False, "dotGrid": 0}, "blocks": blocks}


def make_key_moment_slide(moment: dict[str, Any], idx: int) -> dict[str, Any]:
    """Build one key-moment slide for a finished render."""
    timestamp = float(moment.get("timestamp", 0.0) or 0.0)
    caption = moment.get("caption", "") or ""
    title = moment.get("title") or caption[:60]
    eyebrow = f"KEY MOMENT {idx:02d}"
    if timestamp:
        eyebrow += f" @ {int(timestamp // 60):02d}:{int(timestamp % 60):02d}"
    blocks: list[dict[str, Any]] = []
    _standard_header(blocks, eyebrow, title)
    blocks.append({"id": _gen_id(), "type": "text", "x": 36, "y": 150, "w": 1128,
                   "props": {"text": caption, "fontSize": 19, "weight": 400, "color": _BRAND_BLACK,
                             "family": "sans", "align": "left", "lineHeight": 1.5}})
    if moment.get("image_url"):
        blocks.append({"id": _gen_id(), "type": "image", "x": 36, "y": 230, "w": 1128, "h": 400,
                       "props": {"src": moment["image_url"], "fit": "cover"}})
    blocks.append(_bottom_bar())
    return {"id": _gen_id(), "background": {"color": "#FFFFFF", "inset": False, "dotGrid": 0}, "blocks": blocks}


def scene_plan_to_deck(scene_plan: dict[str, Any], title: str = "Storyboard", project: str = "", placeholders: dict[str, str] | None = None) -> dict[str, Any]:
    """Convert a scene_plan artifact into a Workspace Slides deck."""
    placeholders = placeholders or {}
    deck: dict[str, Any] = {
        "themeVersion": "workspace.1", "project": project,
        "derived_from": scene_plan.get("id", "scene_plan"),
        "slides": [make_title_slide(title, subtitle="Review scenes before asset generation")],
    }
    for idx, scene in enumerate(scene_plan.get("scenes", []), start=1):
        scene_id = scene.get("id") or str(idx)
        deck["slides"].append(make_scene_slide(scene, idx, placeholders.get(scene_id)))
    return deck


def key_moments_to_deck(key_moments: list[dict[str, Any]], title: str = "Key Moments", project: str = "", render_path: str = "") -> dict[str, Any]:
    """Convert sampled key moments into a shareable Workspace Slides deck."""
    deck: dict[str, Any] = {
        "themeVersion": "workspace.1", "project": project,
        "derived_from_render_report": render_path,
        "slides": [make_title_slide(title, subtitle="A shareable summary of the finished render")],
    }
    for idx, moment in enumerate(key_moments, start=1):
        deck["slides"].append(make_key_moment_slide(moment, idx))
    return deck


class SlidesAdapter(BaseTool):
    """OpenMontage <-> Workspace Slides conversion tool."""

    name = "SlidesAdapter"
    version = "1.0.0"
    tier = ToolTier.PUBLISH
    stability = ToolStability.BETA
    runtime = ToolRuntime.LOCAL
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.DETERMINISTIC
    resource_profile = ResourceProfile(cpu_cores=1, ram_mb=256, disk_mb=10, network_required=False)
    capability = "presentation"
    provider = "openmontage"
    supports = {
        "scene_plan_to_deck": "Build a storyboard deck from a scene_plan artifact",
        "key_moments_to_deck": "Build a key-moments deck from sampled frames + captions",
        "create_title_slide": "Return a Workspace-Slides-compatible title slide",
        "create_content_slide": "Return a Workspace-Slides-compatible content slide",
        "save_deck": "Persist deck JSON to disk",
        "load_deck": "Load deck JSON from disk",
    }
    best_for = ["storyboard review before asset generation", "key-moment slide decks after rendering"]

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        return 0.0

    def estimate_runtime(self, inputs: dict[str, Any]) -> float:
        return 0.1

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        action = inputs.get("action")
        if not action:
            return ToolResult(success=False, error="missing required 'action' field")
        try:
            if action == "scene_plan_to_deck":
                return ToolResult(success=True, data={"deck": scene_plan_to_deck(inputs["scene_plan"], inputs.get("title", "Storyboard"), inputs.get("project", ""), inputs.get("placeholders"))})
            if action == "key_moments_to_deck":
                return ToolResult(success=True, data={"deck": key_moments_to_deck(inputs.get("key_moments", []), inputs.get("title", "Key Moments"), inputs.get("project", ""), inputs.get("render_path", ""))})
            if action == "create_title_slide":
                return ToolResult(success=True, data={"slide": make_title_slide(inputs["title"], inputs.get("subtitle", ""))})
            if action == "create_content_slide":
                return ToolResult(success=True, data={"slide": make_content_slide(inputs.get("eyebrow", ""), inputs.get("headline", ""), inputs.get("body", ""))})
            if action == "save_deck":
                path = Path(inputs["path"])
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(inputs["deck"], indent=2), encoding="utf-8")
                return ToolResult(success=True, data={"path": str(path)})
            if action == "load_deck":
                path = Path(inputs["path"])
                return ToolResult(success=True, data={"deck": json.loads(path.read_text(encoding="utf-8"))})
            return ToolResult(success=False, error=f"unknown action: {action!r}")
        except KeyError as exc:
            return ToolResult(success=False, error=f"missing required field for action '{action}': {exc}")
        except Exception as exc:
            return ToolResult(success=False, error=f"{type(exc).__name__}: {exc}")
