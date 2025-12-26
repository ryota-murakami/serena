"""Symbol tools with minimized docstrings for context optimization"""

import os
from collections.abc import Sequence
from copy import copy
from typing import Any

from serena.tools import (
    SUCCESS_RESULT,
    Tool,
    ToolMarkerSymbolicEdit,
    ToolMarkerSymbolicRead,
)
from serena.tools.tools_base import ToolMarkerOptional
from solidlsp.ls_types import SymbolKind


def _sanitize_symbol_dict(symbol_dict: dict[str, Any]) -> dict[str, Any]:
    symbol_dict = copy(symbol_dict)
    s_relative_path = symbol_dict.get("location", {}).get("relative_path")
    if s_relative_path is not None:
        symbol_dict["relative_path"] = s_relative_path
    symbol_dict.pop("location", None)
    symbol_dict.pop("name")
    return symbol_dict


class RestartLanguageServerTool(Tool, ToolMarkerOptional):
    """Restart language server if it hangs."""

    def apply(self) -> str:
        """Restart LSP. Use only on explicit request."""
        self.agent.reset_language_server_manager()
        return SUCCESS_RESULT


class GetSymbolsOverviewTool(Tool, ToolMarkerSymbolicRead):
    """Get file's top-level symbols."""

    def apply(self, relative_path: str, depth: int = 0, max_answer_chars: int = -1) -> str:
        """Get symbols overview for a file."""
        symbol_retriever = self.create_language_server_symbol_retriever()
        file_path = os.path.join(self.project.project_root, relative_path)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {relative_path} does not exist.")
        if os.path.isdir(file_path):
            raise ValueError(f"Expected file, got directory: {relative_path}")
        result = symbol_retriever.get_symbol_overview(relative_path, depth=depth)[relative_path]
        result_json_str = self._to_json(result)
        return self._limit_length(result_json_str, max_answer_chars)


class FindSymbolTool(Tool, ToolMarkerSymbolicRead):
    """Search symbols by name pattern using LSP."""

    def apply(
        self,
        name_path_pattern: str,
        depth: int = 0,
        relative_path: str = "",
        include_body: bool = False,
        include_kinds: list[int] = [],
        exclude_kinds: list[int] = [],
        substring_matching: bool = False,
        max_answer_chars: int = -1,
    ) -> str:
        """Search symbols by pattern. Returns locations."""
        parsed_include_kinds: Sequence[SymbolKind] | None = [SymbolKind(k) for k in include_kinds] if include_kinds else None
        parsed_exclude_kinds: Sequence[SymbolKind] | None = [SymbolKind(k) for k in exclude_kinds] if exclude_kinds else None
        symbol_retriever = self.create_language_server_symbol_retriever()
        symbols = symbol_retriever.find(
            name_path_pattern,
            include_kinds=parsed_include_kinds,
            exclude_kinds=parsed_exclude_kinds,
            substring_matching=substring_matching,
            within_relative_path=relative_path,
        )
        symbol_dicts = [_sanitize_symbol_dict(s.to_dict(kind=True, location=True, depth=depth, include_body=include_body)) for s in symbols]
        result = self._to_json(symbol_dicts)
        return self._limit_length(result, max_answer_chars)


class FindReferencingSymbolsTool(Tool, ToolMarkerSymbolicRead):
    """Find symbols referencing a target symbol."""

    def apply(
        self,
        name_path: str,
        relative_path: str,
        include_kinds: list[int] = [],
        exclude_kinds: list[int] = [],
        max_answer_chars: int = -1,
    ) -> str:
        """Find references to symbol. Returns locations with snippets."""
        include_body = False
        parsed_include_kinds: Sequence[SymbolKind] | None = [SymbolKind(k) for k in include_kinds] if include_kinds else None
        parsed_exclude_kinds: Sequence[SymbolKind] | None = [SymbolKind(k) for k in exclude_kinds] if exclude_kinds else None
        symbol_retriever = self.create_language_server_symbol_retriever()
        references_in_symbols = symbol_retriever.find_referencing_symbols(
            name_path,
            relative_file_path=relative_path,
            include_body=include_body,
            include_kinds=parsed_include_kinds,
            exclude_kinds=parsed_exclude_kinds,
        )
        reference_dicts = []
        for ref in references_in_symbols:
            ref_dict = ref.symbol.to_dict(kind=True, location=True, depth=0, include_body=include_body)
            ref_dict = _sanitize_symbol_dict(ref_dict)
            if not include_body:
                ref_relative_path = ref.symbol.location.relative_path
                assert ref_relative_path is not None
                content_around_ref = self.project.retrieve_content_around_line(
                    relative_file_path=ref_relative_path, line=ref.line, context_lines_before=1, context_lines_after=1
                )
                ref_dict["content_around_reference"] = content_around_ref.to_display_string()
            reference_dicts.append(ref_dict)
        result = self._to_json(reference_dicts)
        return self._limit_length(result, max_answer_chars)


class RenameSymbolTool(Tool, ToolMarkerSymbolicEdit):
    """Rename symbol across codebase."""

    def apply(self, name_path: str, relative_path: str, new_name: str) -> str:
        """Rename symbol throughout codebase using LSP."""
        code_editor = self.create_code_editor()
        status_message = code_editor.rename_symbol(name_path, relative_file_path=relative_path, new_name=new_name)
        return status_message
