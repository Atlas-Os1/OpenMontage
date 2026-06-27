"""Cloudflare Workers AI image generation.

Two transport modes, auto-selected:

1. Worker proxy (preferred) - if CLOUDFLARE_AI_PROXY_URL is set, POST an
   OpenAI-style request to ``{proxy}/v1/images/generations`` and read
   ``data[0].b64_json``. Optional bearer auth via CLOUDFLARE_AI_PROXY_SECRET.
2. Direct Workers AI REST (fallback) - POST to
   ``/accounts/{account}/ai/run/{model}`` with the Workers AI token. FLUX
   returns ``result.image`` as a base64 JPEG.

Set in .env:
    CLOUDFLARE_ACCOUNT_ID=...
    CLOUDFLARE_WORKERS_AI_TOKEN=...
    CLOUDFLARE_AI_PROXY_URL=        # optional, e.g. https://om-ai.<sub>.workers.dev
    CLOUDFLARE_AI_PROXY_SECRET=     # optional bearer for the proxy
"""

from __future__ import annotations

import base64
import os
import time
from pathlib import Path
from typing import Any

from tools.base_tool import (
    BaseTool,
    Determinism,
    ExecutionMode,
    ResourceProfile,
    RetryPolicy,
    ToolResult,
    ToolRuntime,
    ToolStability,
    ToolStatus,
    ToolTier,
)

# Native Workers AI text-to-image models (callable via /ai/run/{model}).
_MODEL_ALIASES = {
    "flux-schnell": "@cf/black-forest-labs/flux-1-schnell",
    "flux": "@cf/black-forest-labs/flux-1-schnell",
    "sdxl": "@cf/stabilityai/stable-diffusion-xl-base-1.0",
    "sdxl-lightning": "@cf/bytedance/stable-diffusion-xl-lightning",
    "dreamshaper": "@cf/lykon/dreamshaper-8-lcm",
}
_DEFAULT_MODEL = "flux-schnell"


class CloudflareImage(BaseTool):
    name = "cloudflare_image"
    version = "0.1.0"
    tier = ToolTier.GENERATE
    capability = "image_generation"
    provider = "cloudflare"
    stability = ToolStability.BETA
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.SEEDED
    runtime = ToolRuntime.API

    dependencies = []  # checked dynamically via env vars
    install_instructions = (
        "Set CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_WORKERS_AI_TOKEN in .env "
        "(Workers AI plan). Optionally set CLOUDFLARE_AI_PROXY_URL to route "
        "through an OpenAI-compatible Worker proxy."
    )
    agent_skills = ["flux-best-practices", "bfl-api"]

    capabilities = ["generate_image", "generate_illustration", "text_to_image"]
    supports = {
        "negative_prompt": True,
        "seed": True,
        "custom_size": True,
    }
    best_for = [
        "fast, low-cost FLUX images on a Workers AI plan",
        "general-purpose image generation without a separate paid key",
        "image assets when Cloudflare is the primary provider",
    ]
    not_good_for = ["text rendering in images", "offline generation"]

    input_schema = {
        "type": "object",
        "required": ["prompt"],
        "properties": {
            "prompt": {"type": "string"},
            "negative_prompt": {"type": "string", "default": ""},
            "width": {"type": "integer", "default": 1024},
            "height": {"type": "integer", "default": 1024},
            "model": {
                "type": "string",
                "enum": list(_MODEL_ALIASES.keys()),
                "default": _DEFAULT_MODEL,
            },
            "seed": {"type": "integer"},
            "num_inference_steps": {"type": "integer"},
            "guidance_scale": {"type": "number"},
            "output_path": {"type": "string"},
        },
    }

    resource_profile = ResourceProfile(
        cpu_cores=1, ram_mb=512, vram_mb=0, disk_mb=100, network_required=True
    )
    retry_policy = RetryPolicy(max_retries=2, retryable_errors=["rate_limit", "timeout"])
    idempotency_key_fields = ["prompt", "width", "height", "seed", "model"]
    side_effects = ["writes image file to output_path", "calls Cloudflare Workers AI"]
    user_visible_verification = ["Inspect generated image for relevance and quality"]

    # --- availability ---------------------------------------------------
    def _account_id(self) -> str | None:
        return os.environ.get("CLOUDFLARE_ACCOUNT_ID")

    def _ai_token(self) -> str | None:
        return os.environ.get("CLOUDFLARE_WORKERS_AI_TOKEN") or os.environ.get(
            "CLOUDFLARE_API_TOKEN"
        )

    def _proxy_url(self) -> str | None:
        url = os.environ.get("CLOUDFLARE_AI_PROXY_URL")
        return url.rstrip("/") if url else None

    def get_status(self) -> ToolStatus:
        if self._proxy_url():
            return ToolStatus.AVAILABLE
        if self._account_id() and self._ai_token():
            return ToolStatus.AVAILABLE
        return ToolStatus.UNAVAILABLE

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        # Workers AI is billed in neurons under the plan; effectively ~free
        # per image at typical resolutions. Report a tiny nominal cost.
        return 0.001

    # --- execution ------------------------------------------------------
    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        if self.get_status() != ToolStatus.AVAILABLE:
            return ToolResult(success=False, error="Cloudflare not configured. " + self.install_instructions)

        import requests

        start = time.time()
        prompt = inputs["prompt"]
        alias = inputs.get("model", _DEFAULT_MODEL)
        model = _MODEL_ALIASES.get(alias, alias)
        width = int(inputs.get("width", 1024))
        height = int(inputs.get("height", 1024))
        seed = inputs.get("seed")

        try:
            img_bytes = (
                self._via_proxy(requests, prompt, model, width, height, seed, inputs)
                if self._proxy_url()
                else self._via_rest(requests, prompt, model, width, height, seed, inputs)
            )
        except Exception as e:  # noqa: BLE001
            return ToolResult(success=False, error=f"Cloudflare image generation failed: {e}")

        output_path = Path(inputs.get("output_path", "generated_image.png"))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(img_bytes)

        return ToolResult(
            success=True,
            data={
                "provider": "cloudflare",
                "transport": "proxy" if self._proxy_url() else "workers-ai-rest",
                "model": model,
                "prompt": prompt,
                "output": str(output_path),
                "seed": seed,
            },
            artifacts=[str(output_path)],
            cost_usd=self.estimate_cost(inputs),
            duration_seconds=round(time.time() - start, 2),
            seed=seed,
            model=f"cloudflare/{model}",
        )

    def _via_rest(self, requests, prompt, model, width, height, seed, inputs) -> bytes:
        acct = self._account_id()
        token = self._ai_token()
        payload: dict[str, Any] = {"prompt": prompt, "width": width, "height": height}
        if seed is not None:
            payload["seed"] = seed
        if inputs.get("num_inference_steps"):
            payload["steps"] = inputs["num_inference_steps"]
        if inputs.get("guidance_scale"):
            payload["guidance"] = inputs["guidance_scale"]
        if inputs.get("negative_prompt"):
            payload["negative_prompt"] = inputs["negative_prompt"]

        resp = requests.post(
            f"https://api.cloudflare.com/client/v4/accounts/{acct}/ai/run/{model}",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=payload,
            timeout=120,
        )
        ct = resp.headers.get("content-type", "")
        if resp.status_code != 200:
            raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:300]}")
        # Some models stream raw image bytes; FLUX returns JSON with base64.
        if "application/json" in ct:
            data = resp.json()
            if not data.get("success", True):
                raise RuntimeError(str(data.get("errors") or data))
            result = data.get("result", {})
            b64 = result.get("image") if isinstance(result, dict) else None
            if not b64:
                raise RuntimeError(f"No image in response: {str(data)[:300]}")
            return base64.b64decode(b64)
        return resp.content

    def _via_proxy(self, requests, prompt, model, width, height, seed, inputs) -> bytes:
        url = self._proxy_url() + "/v1/images/generations"
        headers = {"Content-Type": "application/json"}
        secret = os.environ.get("CLOUDFLARE_AI_PROXY_SECRET")
        if secret:
            headers["Authorization"] = f"Bearer {secret}"
        payload = {
            "model": model,
            "prompt": prompt,
            "size": f"{width}x{height}",
            "response_format": "b64_json",
        }
        if seed is not None:
            payload["seed"] = seed
        if inputs.get("negative_prompt"):
            payload["negative_prompt"] = inputs["negative_prompt"]
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        if resp.status_code != 200:
            raise RuntimeError(f"proxy HTTP {resp.status_code}: {resp.text[:300]}")
        data = resp.json()
        item = data["data"][0]
        if item.get("b64_json"):
            return base64.b64decode(item["b64_json"])
        if item.get("url"):
            img = requests.get(item["url"], timeout=60)
            img.raise_for_status()
            return img.content
        raise RuntimeError(f"No image in proxy response: {str(data)[:300]}")
