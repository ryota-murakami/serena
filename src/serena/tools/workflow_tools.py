"""Workflow tools with minimized docstrings for context optimization"""

import json
import platform

from serena.tools import Tool, ToolMarkerDoesNotRequireActiveProject, ToolMarkerOptional


class CheckOnboardingPerformedTool(Tool):
    """Check if onboarding is complete."""

    def apply(self) -> str:
        """Check onboarding status. Call before starting work."""
        from .memory_tools import ListMemoriesTool
        list_memories_tool = self.agent.get_tool(ListMemoriesTool)
        memories = json.loads(list_memories_tool.apply())
        if len(memories) == 0:
            return "Onboarding not performed. Call `onboarding` tool first."
        else:
            return f"Onboarding complete. Available memories: {memories}"


class OnboardingTool(Tool):
    """Perform project onboarding."""

    def apply(self) -> str:
        """Call if onboarding not yet performed."""
        system = platform.system()
        return self.prompt_factory.create_onboarding_prompt(system=system)


class ThinkAboutCollectedInformationTool(Tool):
    """Reflect on collected information."""

    def apply(self) -> str:
        """Call after search sequences to assess completeness."""
        return self.prompt_factory.create_think_about_collected_information()


class ThinkAboutTaskAdherenceTool(Tool):
    """Check if still on track."""

    def apply(self) -> str:
        """Call before code edits."""
        return self.prompt_factory.create_think_about_task_adherence()


class ThinkAboutWhetherYouAreDoneTool(Tool):
    """Check if task is complete."""

    def apply(self) -> str:
        """Call when you think you're done."""
        return self.prompt_factory.create_think_about_whether_you_are_done()


class SummarizeChangesTool(Tool, ToolMarkerOptional):
    """Summarize changes made."""

    def apply(self) -> str:
        """Summarize after completing tasks."""
        return self.prompt_factory.create_summarize_changes()


class PrepareForNewConversationTool(Tool):
    """Prepare for new conversation."""

    def apply(self) -> str:
        """Call on explicit user request only."""
        return self.prompt_factory.create_prepare_for_new_conversation()


class InitialInstructionsTool(Tool, ToolMarkerDoesNotRequireActiveProject):
    """Get Serena instructions manual."""

    def apply(self) -> str:
        """Get essential Serena usage instructions."""
        return self.agent.create_system_prompt()
