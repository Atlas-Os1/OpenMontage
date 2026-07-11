"""Hermes tool schemas for the OpenMontage provider layer."""

PROVIDER_INVENTORY = {
    "name": "openmontage_provider_inventory",
    "description": "Return the configured OpenMontage provider and model catalog without exposing secret values.",
    "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
}

PROVIDER_STATUS = {
    "name": "openmontage_provider_status",
    "description": "Check which OpenMontage provider credentials and runtime paths are available; never return secret values.",
    "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
}

IMAGE_GENERATE = {
    "name": "openmontage_generate_image",
    "description": "Generate an image through the verified Cloudflare AI Gateway or Workers AI route, save it locally, and return artifact metadata.",
    "parameters": {
        "type": "object",
        "properties": {
            "prompt": {"type": "string"},
            "model": {"type": "string", "default": "google/nano-banana-2"},
            "output_path": {"type": "string"},
            "aspect_ratio": {"type": "string", "default": "16:9"},
            "output_format": {"type": "string", "enum": ["png", "jpg"], "default": "png"},
            "resolution": {"type": "string", "enum": ["1K", "2K", "4K"]},
            "image_input": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["prompt"],
        "additionalProperties": False,
    },
}

VOICE_GENERATE = {
    "name": "openmontage_generate_voice",
    "description": "Generate narration with ElevenLabs, save it locally, and return artifact metadata.",
    "parameters": {
        "type": "object",
        "properties": {
            "text": {"type": "string"},
            "voice_id": {"type": "string"},
            "model_id": {"type": "string", "default": "eleven_multilingual_v2"},
            "output_path": {"type": "string"},
            "output_format": {"type": "string", "default": "mp3_44100_128"},
            "stability": {"type": "number", "minimum": 0, "maximum": 1},
            "similarity_boost": {"type": "number", "minimum": 0, "maximum": 1},
            "style": {"type": "number", "minimum": 0, "maximum": 1},
        },
        "required": ["text"],
        "additionalProperties": False,
    },
}

VIDEO_GENERATE = {
    "name": "openmontage_generate_video",
    "description": "Generate or rank video providers through OpenMontage's existing VideoSelector and return verified local/R2 artifact metadata.",
    "parameters": {
        "type": "object",
        "properties": {
            "prompt": {"type": "string"},
            "operation": {"type": "string", "enum": ["text_to_video", "image_to_video", "reference_to_video", "rank"], "default": "text_to_video"},
            "preferred_provider": {"type": "string", "default": "auto"},
            "allowed_providers": {"type": "array", "items": {"type": "string"}},
            "aspect_ratio": {"type": "string", "default": "16:9"},
            "duration": {"type": "string", "default": "5"},
            "resolution": {"type": "string"},
            "reference_image_url": {"type": "string"},
            "reference_image_path": {"type": "string"},
            "output_path": {"type": "string"},
        },
        "required": ["prompt"],
        "additionalProperties": False,
    },
}

TOOL_CATALOG = {
    "name": "openmontage_tool_catalog",
    "description": "List the complete OpenMontage editing tool catalog, declared input schemas, capabilities, and source files without importing optional ML dependencies.",
    "parameters": {"type": "object", "properties": {"capability": {"type": "string"}}, "additionalProperties": False},
}

EXECUTE_TOOL = {
    "name": "openmontage_execute_tool",
    "description": "Execute an existing OpenMontage BaseTool by its catalog name. Use openmontage_tool_catalog first when the exact tool/input schema is unknown.",
    "parameters": {
        "type": "object",
        "properties": {"tool_name": {"type": "string"}, "inputs": {"type": "object"}},
        "required": ["tool_name"],
        "additionalProperties": False,
    },
}

PREFLIGHT = {
    "name": "openmontage_preflight_edit",
    "description": "Run a non-generative OpenMontage editing preflight for engine, FFmpeg, project/input paths, and skill-pack availability.",
    "parameters": {
        "type": "object",
        "properties": {"operation": {"type": "string"}, "project_path": {"type": "string"}, "input_path": {"type": "string"}},
        "additionalProperties": False,
    },
}

MODEL_ROUTE = {
    "name": "openmontage_model_route",
    "description": "Recommend a provider and model for a media department using the OpenMontage routing catalog.",
    "parameters": {
        "type": "object",
        "properties": {
            "department": {
                "type": "string",
                "enum": ["image_generation", "image_editing", "image_understanding", "video_generation", "video_editing", "voice", "stock_media", "text", "embeddings", "rendering"],
            },
            "quality": {"type": "string", "enum": ["draft", "standard", "premium"]},
            "lane": {"type": "string", "enum": ["local", "atlas-content"]},
        },
        "required": ["department"],
        "additionalProperties": False,
    },
}
