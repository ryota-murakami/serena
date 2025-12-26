"""Memory tools with minimized docstrings for context optimization"""

from typing import Literal
from serena.tools import ReplaceContentTool, Tool


class WriteMemoryTool(Tool):
    """Save named memory for future reference."""

    def apply(self, memory_file_name: str, content: str, max_answer_chars: int = -1) -> str:
        """Write memory to project store."""
        if max_answer_chars == -1:
            max_answer_chars = self.agent.serena_config.default_max_tool_answer_chars
        if len(content) > max_answer_chars:
            raise ValueError(f"Content too long. Max: {max_answer_chars}")
        return self.memories_manager.save_memory(memory_file_name, content)


class ReadMemoryTool(Tool):
    """Read memory from project store."""

    def apply(self, memory_file_name: str, max_answer_chars: int = -1) -> str:
        """Read memory. Only if relevant to current task."""
        return self.memories_manager.load_memory(memory_file_name)


class ListMemoriesTool(Tool):
    """List available memories."""

    def apply(self) -> str:
        """List all memories."""
        return self._to_json(self.memories_manager.list_memories())


class DeleteMemoryTool(Tool):
    """Delete memory from store."""

    def apply(self, memory_file_name: str) -> str:
        """Delete memory. Only on explicit user request."""
        return self.memories_manager.delete_memory(memory_file_name)


class EditMemoryTool(Tool):
    """Edit memory content."""

    def apply(
        self,
        memory_file_name: str,
        needle: str,
        repl: str,
        mode: Literal["literal", "regex"],
    ) -> str:
        """Replace content in memory."""
        replace_content_tool = self.agent.get_tool(ReplaceContentTool)
        rel_path = self.memories_manager.get_memory_file_path(memory_file_name).relative_to(self.get_project_root())
        return replace_content_tool.replace_content(str(rel_path), needle, repl, mode=mode, require_not_ignored=False)
