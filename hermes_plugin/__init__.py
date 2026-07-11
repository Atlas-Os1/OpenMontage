"""Hermes plugin adapter for OpenMontage provider routing."""

from . import schemas, tools


def register(ctx):
    ctx.register_tool(
        name="openmontage_provider_inventory",
        toolset="openmontage",
        schema=schemas.PROVIDER_INVENTORY,
        handler=lambda args, **kwargs: tools.provider_inventory(**(args or {})),
    )
    ctx.register_tool(
        name="openmontage_provider_status",
        toolset="openmontage",
        schema=schemas.PROVIDER_STATUS,
        handler=lambda args, **kwargs: tools.provider_status(**(args or {})),
    )
    ctx.register_tool(
        name="openmontage_model_route",
        toolset="openmontage",
        schema=schemas.MODEL_ROUTE,
        handler=lambda args, **kwargs: tools.model_route(**(args or {})),
    )
    ctx.register_tool(
        name="openmontage_generate_image",
        toolset="openmontage",
        schema=schemas.IMAGE_GENERATE,
        handler=lambda args, **kwargs: tools.generate_image(**(args or {})),
    )
    ctx.register_tool(
        name="openmontage_generate_voice",
        toolset="openmontage",
        schema=schemas.VOICE_GENERATE,
        handler=lambda args, **kwargs: tools.generate_voice(**(args or {})),
    )
    ctx.register_tool(
        name="openmontage_generate_video",
        toolset="openmontage",
        schema=schemas.VIDEO_GENERATE,
        handler=lambda args, **kwargs: tools.generate_video(**(args or {})),
    )
    ctx.register_tool(
        name="openmontage_tool_catalog",
        toolset="openmontage",
        schema=schemas.TOOL_CATALOG,
        handler=lambda args, **kwargs: tools.tool_catalog(**(args or {})),
    )
    ctx.register_tool(
        name="openmontage_execute_tool",
        toolset="openmontage",
        schema=schemas.EXECUTE_TOOL,
        handler=lambda args, **kwargs: tools.execute_engine_tool(**(args or {})),
    )
    ctx.register_tool(
        name="openmontage_preflight_edit",
        toolset="openmontage",
        schema=schemas.PREFLIGHT,
        handler=lambda args, **kwargs: tools.preflight_edit(**(args or {})),
    )
