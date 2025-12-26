"""Config tools with minimized docstrings for context optimization"""

from serena.config.context_mode import SerenaAgentMode
from serena.tools import Tool, ToolMarkerDoesNotRequireActiveProject, ToolMarkerOptional


class ActivateProjectTool(Tool, ToolMarkerDoesNotRequireActiveProject):
    """Activate project by name or path."""

    def apply(self, project: str) -> str:
        """Activate project."""
        active_project = self.agent.activate_project_from_path_or_name(project)
        result = active_project.get_activation_message()
        result += "\nIMPORTANT: If you have not yet read the 'Serena Instructions Manual', do it now before continuing!"
        return result


class RemoveProjectTool(Tool, ToolMarkerDoesNotRequireActiveProject, ToolMarkerOptional):
    """Remove project from config."""

    def apply(self, project_name: str) -> str:
        """Remove project."""
        self.agent.serena_config.remove_project(project_name)
        return f"Removed project '{project_name}'."


class SwitchModesTool(Tool, ToolMarkerOptional):
    """Switch operation modes."""

    def apply(self, modes: list[str]) -> str:
        """Activate modes like ['editing', 'interactive']."""
        mode_instances = [SerenaAgentMode.load(mode) for mode in modes]
        self.agent.set_modes(mode_instances)
        result_str = f"Activated modes: {', '.join([mode.name for mode in mode_instances])}\n"
        result_str += "\n".join([mode_instance.prompt for mode_instance in mode_instances]) + "\n"
        result_str += f"Active tools: {', '.join(self.agent.get_active_tool_names())}"
        return result_str
