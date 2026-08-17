"""Tests for tools/presentation/slides_adapter.py"""

import json
from pathlib import Path

import pytest

from tools.presentation.slides_adapter import SlidesAdapter, make_content_slide, make_scene_slide, make_title_slide, scene_plan_to_deck


def _valid_block(block: dict) -> None:
    assert isinstance(block["id"], str) and block["id"]
    assert isinstance(block["type"], str)
    assert isinstance(block["x"], (int, float))
    assert isinstance(block["y"], (int, float))


def _valid_deck(deck: dict) -> None:
    assert deck.get("themeVersion") == "workspace.1"
    assert isinstance(deck.get("slides"), list)
    for slide in deck["slides"]:
        assert isinstance(slide["id"], str) and slide["id"]
        assert isinstance(slide["background"], dict)
        assert isinstance(slide["blocks"], list)
        for block in slide["blocks"]:
            _valid_block(block)


@pytest.fixture
def sample_scene_plan():
    return {"id": "sp-demo", "scenes": [
        {"id": "s01", "start_time": 0.0, "duration": 5.0, "description": "Hero title establishes the topic", "narration": "Welcome to the explainer.", "required_assets": []},
        {"id": "s02", "start_time": 5.0, "duration": 6.0, "description": "An animated diagram shows the flow", "narration": "Data flows from source to destination.", "required_assets": []},
    ]}


def test_make_title_slide():
    slide = make_title_slide("OpenMontage", subtitle="Subtitle text")
    assert slide["background"]["color"] == "#F6821F"
    types = [b["type"] for b in slide["blocks"]]
    assert "logo" in types and "title" in types and "subtitle" in types


def test_make_content_slide():
    types = [b["type"] for b in make_content_slide("EYEBROW", "Headline", "Body copy")["blocks"]]
    assert "sectionLabel" in types and "title" in types and "text" in types and "svg" in types


def test_make_scene_slide():
    slide = make_scene_slide({"id": "s01", "start_time": 1.5, "duration": 4.0, "description": "Description text", "narration": "Narration text"}, 1, "@url:`http://example.com/a.png`")
    types = [b["type"] for b in slide["blocks"]]
    assert "sectionLabel" in types and "image" in types
    _valid_deck({"themeVersion": "workspace.1", "slides": [slide]})


def test_scene_plan_to_deck(sample_scene_plan):
    deck = scene_plan_to_deck(sample_scene_plan, title="Test Storyboard", project="demo")
    _valid_deck(deck)
    assert len(deck["slides"]) == 3
    assert deck["project"] == "demo" and deck["derived_from"] == "sp-demo"


def test_slides_adapter_scene_plan_to_deck(sample_scene_plan):
    result = SlidesAdapter().execute({"action": "scene_plan_to_deck", "scene_plan": sample_scene_plan, "title": "Adapter Storyboard", "project": "demo"})
    assert result.success
    _valid_deck(result.data["deck"])


def test_slides_adapter_save_and_load_deck(tmp_path: Path, sample_scene_plan):
    tool = SlidesAdapter()
    path = tmp_path / "deck.json"
    assert tool.execute({"action": "save_deck", "deck": scene_plan_to_deck(sample_scene_plan), "path": str(path)}).success
    assert json.loads(path.read_text())["project"] == ""
    loaded = tool.execute({"action": "load_deck", "path": str(path)})
    assert loaded.success
    _valid_deck(loaded.data["deck"])


def test_slides_adapter_unknown_action():
    result = SlidesAdapter().execute({"action": "not_real"})
    assert not result.success and "unknown action" in result.error.lower()


def test_animated_explainer_manifest_has_storyboard_stage():
    text = (Path(__file__).resolve().parents[2] / "pipeline_defs" / "animated-explainer.yaml").read_text(encoding="utf-8")
    assert "name: storyboard" in text and "storyboard-director" in text and "scene_plan_deck" in text


def test_make_key_moment_slide():
    from tools.presentation.slides_adapter import make_key_moment_slide
    slide = make_key_moment_slide({"timestamp": 5.0, "caption": "The narrator introduces the core concept.", "title": "Core concept", "image_url": "@url:`http://example.com/frame.png`"}, 1)
    types = [b["type"] for b in slide["blocks"]]
    assert "sectionLabel" in types and "image" in types


def test_key_moments_to_deck():
    from tools.presentation.slides_adapter import key_moments_to_deck
    deck = key_moments_to_deck([
        {"timestamp": 0.0, "caption": "Opening hook", "image_url": "@url:`http://example.com/0.png`"},
        {"timestamp": 10.0, "caption": "The payoff", "image_url": "@url:`http://example.com/10.png`"},
    ], title="Key Moments", project="demo", render_path="final.mp4")
    _valid_deck(deck)
    assert len(deck["slides"]) == 3 and deck["derived_from_render_report"] == "final.mp4"


def test_slides_adapter_key_moments_to_deck():
    result = SlidesAdapter().execute({"action": "key_moments_to_deck", "key_moments": [{"timestamp": 3.0, "caption": "A key point", "image_url": "a.png"}], "title": "Adapter Key Moments", "project": "demo", "render_path": "out.mp4"})
    assert result.success
    _valid_deck(result.data["deck"])


def test_animated_explainer_manifest_has_publish_deck_stage():
    text = (Path(__file__).resolve().parents[2] / "pipeline_defs" / "animated-explainer.yaml").read_text(encoding="utf-8")
    assert "name: publish_deck" in text and "publish-deck-director" in text and "key_moments_deck" in text
