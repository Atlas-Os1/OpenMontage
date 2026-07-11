"""Provider inventory and routing tools for the OpenMontage Hermes plugin."""

from __future__ import annotations

import ast
import base64
import hashlib
import json
import os
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - reported as a structured error
    yaml = None

try:
    from dotenv import dotenv_values
except ImportError:  # pragma: no cover - optional fallback
    dotenv_values = None

PLUGIN_DIR = Path(__file__).resolve().parent
REPO_ROOT = PLUGIN_DIR.parent
CATALOG_PATH = PLUGIN_DIR / "provider_catalog.yaml"
_DOTENV_CACHE: dict[str, str] | None = None


def _engine_root() -> Path:
    configured = os.environ.get("OPENMONTAGE_ROOT")
    marker = PLUGIN_DIR / "openmontage_root.txt"
    if configured:
        return Path(configured).expanduser().resolve()
    if marker.is_file():
        value = marker.read_text(encoding="utf-8").strip()
        if value:
            return Path(value).expanduser().resolve()
    return REPO_ROOT


def _ensure_engine_importable() -> Path:
    root = _engine_root()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    return root


def _static_tool_catalog(capability: str | None = None) -> list[dict[str, Any]]:
    """Read BaseTool declarations without importing optional ML dependencies."""
    root = _engine_root() / "tools"
    rows: list[dict[str, Any]] = []
    if not root.is_dir():
        return rows
    for path in root.rglob("*.py"):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            values: dict[str, Any] = {}
            for child in node.body:
                if isinstance(child, ast.Assign):
                    for target in child.targets:
                        if isinstance(target, ast.Name) and target.id in {"name", "capability", "provider", "tier", "input_schema"}:
                            try:
                                values[target.id] = ast.literal_eval(child.value)
                            except Exception:
                                pass
            if values.get("name") and values.get("capability") and (not capability or values["capability"] == capability):
                rows.append({
                    "name": values["name"],
                    "capability": values["capability"],
                    "provider": values.get("provider", ""),
                    "tier": values.get("tier", ""),
                    "input_schema": values.get("input_schema", {}),
                    "file": str(path.relative_to(root)).replace("\\", "/"),
                })
    return sorted(rows, key=lambda row: (row["capability"], row["name"]))


def _configured_env() -> dict[str, str]:
    """Read presence-only fallback values from owning runtime env files."""
    global _DOTENV_CACHE
    if _DOTENV_CACHE is None:
        values: dict[str, str] = {}
        paths = [REPO_ROOT / ".env"]
        hermes_home = os.environ.get("HERMES_HOME")
        if hermes_home:
            paths.append(Path(hermes_home) / ".env")
        for env_name in ("OPENMONTAGE_ENV_FILE", "HERMES_PROFILE_ENV_FILE"):
            configured = os.environ.get(env_name)
            if configured:
                paths.append(Path(configured))
        if dotenv_values is not None:
            for env_path in paths:
                if env_path.is_file():
                    values.update({k: v or "" for k, v in dotenv_values(env_path).items() if k})
        _DOTENV_CACHE = values
    return _DOTENV_CACHE


def _env_value(name: str) -> str:
    return os.environ.get(name) or _configured_env().get(name, "")

# Names only. Values are intentionally never returned.
SECRET_ENV_NAMES = {
    "CLOUDFLARE_WORKERS_AI_TOKEN", "CLOUDFLARE_API_TOKEN", "CLOUDFLARE_R2_SECRET_ACCESS_KEY",
    "CLOUDFLARE_AI_PROXY_SECRET", "OPENAI_API_KEY", "NVIDIA_API_KEY", "NGC_API_KEY",
    "PEXELS_API_KEY", "PIXABAY_API_KEY", "UNSPLASH_ACCESS_KEY", "ELEVENLABS_API_KEY",
}


def _load_catalog() -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML is required to load provider_catalog.yaml")
    with CATALOG_PATH.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _available(env_names: list[str] | None) -> bool:
    return any(bool(_env_value(name)) for name in (env_names or []))


def _presence(names: list[str] | None) -> dict[str, bool]:
    return {name: bool(_env_value(name)) for name in (names or [])}


def provider_inventory(**_: Any) -> str:
    catalog = _load_catalog()
    providers = {}
    for name, provider in catalog.get("providers", {}).items():
        clean = dict(provider)
        clean["credential_present"] = _available(provider.get("credential_env_any"))
        clean.pop("credential_env_any", None)
        clean.pop("storage_env_any", None)
        clean.pop("secret_env_any", None)
        providers[name] = clean
    return json.dumps({"success": True, "catalog": str(CATALOG_PATH), "providers": providers})


def provider_status(**_: Any) -> str:
    catalog = _load_catalog()
    status = {}
    for name, provider in catalog.get("providers", {}).items():
        credential_names = provider.get("credential_env_any", [])
        required_names = provider.get("required_env", [])
        storage_names = provider.get("storage_env_any", [])
        secret_names = provider.get("secret_env_any", [])
        status[name] = {
            "credential_any_present": _available(credential_names),
            "credentials": _presence(credential_names),
            "required": _presence(required_names),
            "storage_any_present": _available(storage_names),
            "storage": _presence(storage_names),
            "secret_any_present": _available(secret_names),
            "secret": _presence(secret_names),
        }
    return json.dumps({"success": True, "providers": status})


def model_route(department: str, quality: str = "standard", lane: str = "local", **_: Any) -> str:
    catalog = _load_catalog()
    candidates = []
    for provider_name, provider in catalog.get("providers", {}).items():
        if provider_name != "openmontage" and not _available(provider.get("credential_env_any")):
            continue
        route = provider.get("departments", {}).get(department)
        if not route:
            continue
        models = route.get(quality) or route.get("preferred") or []
        for model in models:
            candidates.append({"provider": provider_name, "model": model, "lane": lane})
    return json.dumps({"success": True, "department": department, "quality": quality, "lane": lane, "candidates": candidates})


def tool_catalog(capability: str | None = None, **_: Any) -> str:
    tools = _static_tool_catalog(capability)
    return json.dumps({"success": True, "engine_root": str(_engine_root()), "count": len(tools), "tools": tools}, ensure_ascii=False)


def execute_engine_tool(tool_name: str, inputs: dict[str, Any] | None = None, **_: Any) -> str:
    """Execute any declared OpenMontage BaseTool by name through its registry."""
    _load_runtime_env()
    root = _ensure_engine_importable()
    try:
        from tools.tool_registry import registry
        registry.ensure_discovered()
        tool = registry.get(tool_name)
        if tool is None:
            return json.dumps({"success": False, "error": f"Unknown OpenMontage tool: {tool_name}", "catalog": json.loads(tool_catalog())})
        result = tool.execute(inputs or {})
        return _json_tool_result(result)
    except Exception as exc:
        return json.dumps({"success": False, "tool": tool_name, "engine_root": str(root), "error": str(exc)})


def preflight_edit(operation: str = "doctor", project_path: str | None = None, input_path: str | None = None, **_: Any) -> str:
    """Run a non-generative preflight for the requested editing operation."""
    root = _engine_root()
    checks: dict[str, Any] = {
        "engine_root": str(root),
        "engine_present": (root / "tools").is_dir(),
        "operation": operation,
        "project_present": bool(project_path and Path(project_path).exists()),
        "input_present": bool(input_path and Path(input_path).exists()),
        "ffmpeg_on_path": __import__("shutil").which("ffmpeg") is not None,
        "ffprobe_on_path": __import__("shutil").which("ffprobe") is not None,
        "skill_source_present": (root / ".agents" / "skills").is_dir(),
    }
    checks["ready"] = checks["engine_present"] and checks["ffmpeg_on_path"]
    return json.dumps({"success": True, "preflight": checks})


def _load_runtime_env() -> None:
    """Load configured dotenv values into the process only when executing."""
    for name, value in _configured_env().items():
        if value and not os.environ.get(name):
            os.environ[name] = value


def _json_tool_result(result: Any) -> str:
    payload = asdict(result) if hasattr(result, "__dataclass_fields__") else result
    return json.dumps(payload, ensure_ascii=False, default=str)


def _upload_artifact(path: Path, *, provider: str, model: str) -> dict[str, Any]:
    from tools.publishers.r2_archive import upload_file

    artifact = upload_file(
        path,
        key=f"openmontage/generated/{provider}/{path.name}",
        metadata={"provider": provider, "model": model},
    )
    return artifact.to_dict()


def _decode_media_result(response: Any, requests: Any) -> bytes:
    result = response.get("result", response) if isinstance(response, dict) else response
    if isinstance(result, dict):
        image = result.get("image") or result.get("url")
        if isinstance(image, str) and image.startswith(("http://", "https://")):
            fetched = requests.get(image, timeout=120)
            fetched.raise_for_status()
            return fetched.content
        if isinstance(image, str):
            return base64.b64decode(image)
    raise RuntimeError(f"Cloudflare response did not contain image data: {str(response)[:300]}")


def generate_image(
    prompt: str,
    model: str = "google/nano-banana-2",
    output_path: str = "projects/generated/openmontage-image.png",
    aspect_ratio: str = "16:9",
    output_format: str = "png",
    resolution: str | None = None,
    image_input: list[str] | None = None,
    **_: Any,
) -> str:
    """Generate one verified image through Cloudflare's universal /ai/run endpoint."""
    _load_runtime_env()
    account_id = _env_value("CLOUDFLARE_ACCOUNT_ID")
    token = _env_value("CLOUDFLARE_WORKERS_AI_TOKEN") or _env_value("CLOUDFLARE_API_TOKEN")
    if not account_id or not token:
        return json.dumps({"success": False, "error": "Cloudflare account or AI token is not configured."})

    import requests

    inputs: dict[str, Any] = {
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "output_format": output_format,
    }
    if resolution:
        inputs["resolution"] = resolution
    if image_input:
        inputs["image_input"] = image_input

    started = time.time()
    try:
        response = requests.post(
            f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"model": model, "input": inputs},
            timeout=180,
        )
        response.raise_for_status()
        content = _decode_media_result(response.json(), requests)
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        r2 = _upload_artifact(path, provider="cloudflare", model=model)
        return json.dumps({
            "success": True,
            "provider": "cloudflare",
            "transport": "universal_ai_run",
            "model": model,
            "output": str(path),
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(content).hexdigest(),
            "r2": r2,
            "duration_seconds": round(time.time() - started, 2),
        })
    except Exception as exc:
        return json.dumps({"success": False, "provider": "cloudflare", "model": model, "error": str(exc)})


def generate_voice(
    text: str,
    voice_id: str | None = None,
    model_id: str = "eleven_multilingual_v2",
    output_path: str = "projects/generated/openmontage-voice.mp3",
    output_format: str = "mp3_44100_128",
    stability: float | None = None,
    similarity_boost: float | None = None,
    style: float | None = None,
    **_: Any,
) -> str:
    """Generate narration using OpenMontage's existing ElevenLabs tool."""
    _load_runtime_env()
    if not os.environ.get("ELEVENLABS_API_KEY"):
        return json.dumps({"success": False, "error": "ElevenLabs is not configured in the active runtime."})

    from tools.audio.elevenlabs_tts import ElevenLabsTTS

    inputs: dict[str, Any] = {
        "text": text,
        "model_id": model_id,
        "output_path": output_path,
        "output_format": output_format,
    }
    if voice_id:
        inputs["voice_id"] = voice_id
    if stability is not None:
        inputs["stability"] = stability
    if similarity_boost is not None:
        inputs["similarity_boost"] = similarity_boost
    if style is not None:
        inputs["style"] = style

    tool = ElevenLabsTTS()
    result = tool.execute(inputs)
    if result.success:
        path = Path(output_path)
        result.data["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        result.data["bytes"] = path.stat().st_size
        result.data["r2"] = _upload_artifact(path, provider="elevenlabs", model=model_id)
    return _json_tool_result(result)


def generate_video(
    prompt: str,
    operation: str = "text_to_video",
    preferred_provider: str = "auto",
    allowed_providers: list[str] | None = None,
    aspect_ratio: str = "16:9",
    duration: str = "5",
    resolution: str | None = None,
    reference_image_url: str | None = None,
    reference_image_path: str | None = None,
    output_path: str = "projects/generated/openmontage-video.mp4",
    **_: Any,
) -> str:
    """Delegate video generation/ranking to OpenMontage's existing selector."""
    _load_runtime_env()
    if operation == "rank":
        # Ranking must remain usable even when optional local video dependencies
        # (numpy/torch/diffusers) are not installed in the Hermes runtime.
        return model_route(department="video_generation", quality="standard", lane="local")

    import sys

    repo_root = REPO_ROOT
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    try:
        from tools.video.video_selector import VideoSelector
    except Exception as exc:
        return json.dumps({"success": False, "error": f"OpenMontage video engine unavailable: {exc}"})

    inputs: dict[str, Any] = {
        "prompt": prompt,
        "operation": operation,
        "preferred_provider": preferred_provider,
        "allowed_providers": allowed_providers or [],
        "aspect_ratio": aspect_ratio,
        "duration": duration,
        "output_path": output_path,
    }
    if resolution:
        inputs["resolution"] = resolution
    if reference_image_url:
        inputs["reference_image_url"] = reference_image_url
        inputs["image_url"] = reference_image_url
    if reference_image_path:
        inputs["reference_image_path"] = reference_image_path

    try:
        result = VideoSelector().execute(inputs)
        return _json_tool_result(result)
    except Exception as exc:
        return json.dumps({"success": False, "error": f"OpenMontage video generation failed: {exc}"})
