from typing_extensions import override
from comfy_api.latest import ComfyExtension, io

from .nodes import PlayPromptOutput, ReloadPlayPrompts


class PlayPromptExtension(ComfyExtension):
    @override
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [PlayPromptOutput, ReloadPlayPrompts]


async def comfy_entrypoint() -> PlayPromptExtension:
    return PlayPromptExtension()
