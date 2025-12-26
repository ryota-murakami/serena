"""File tools with minimized docstrings for context optimization"""

import os
import re
from collections import defaultdict
from collections.abc import Callable
from fnmatch import fnmatch
from pathlib import Path
from typing import Literal

from serena.text_utils import search_files
from serena.tools import SUCCESS_RESULT, EditedFileContext, Tool, ToolMarkerCanEdit, ToolMarkerOptional
from serena.util.file_system import scan_directory


class ReadFileTool(Tool):
    """Read file content."""

    def apply(self, relative_path: str, start_line: int = 0, end_line: int | None = None, max_answer_chars: int = -1) -> str:
        """Read file or chunk. Prefer symbolic tools if looking for symbols."""
        self.project.validate_relative_path(relative_path, require_not_ignored=True)
        result = self.project.read_file(relative_path)
        result_lines = result.splitlines()
        if end_line is None:
            result_lines = result_lines[start_line:]
        else:
            result_lines = result_lines[start_line : end_line + 1]
        result = "\n".join(result_lines)
        return self._limit_length(result, max_answer_chars)


class CreateTextFileTool(Tool, ToolMarkerCanEdit):
    """Create or overwrite file."""

    def apply(self, relative_path: str, content: str) -> str:
        """Write new file or overwrite existing."""
        project_root = self.get_project_root()
        abs_path = (Path(project_root) / relative_path).resolve()
        will_overwrite_existing = abs_path.exists()
        if will_overwrite_existing:
            self.project.validate_relative_path(relative_path, require_not_ignored=True)
        else:
            assert abs_path.is_relative_to(self.get_project_root())
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_text(content, encoding=self.project.project_config.encoding)
        answer = f"File created: {relative_path}."
        if will_overwrite_existing:
            answer += " Overwrote existing."
        return answer


class ListDirTool(Tool):
    """List directory contents."""

    def apply(self, relative_path: str, recursive: bool, skip_ignored_files: bool = False, max_answer_chars: int = -1) -> str:
        """List files and directories."""
        if not self.project.relative_path_exists(relative_path):
            error_info = {"error": f"Directory not found: {relative_path}", "project_root": self.get_project_root()}
            return self._to_json(error_info)
        self.project.validate_relative_path(relative_path, require_not_ignored=skip_ignored_files)
        dirs, files = scan_directory(
            os.path.join(self.get_project_root(), relative_path),
            relative_to=self.get_project_root(),
            recursive=recursive,
            is_ignored_dir=self.project.is_ignored_path if skip_ignored_files else None,
            is_ignored_file=self.project.is_ignored_path if skip_ignored_files else None,
        )
        result = self._to_json({"dirs": dirs, "files": files})
        return self._limit_length(result, max_answer_chars)


class FindFileTool(Tool):
    """Find files by mask."""

    def apply(self, file_mask: str, relative_path: str) -> str:
        """Find files matching mask."""
        self.project.validate_relative_path(relative_path, require_not_ignored=True)
        dir_to_scan = os.path.join(self.get_project_root(), relative_path)

        def is_ignored_file(abs_path: str) -> bool:
            if self.project.is_ignored_path(abs_path):
                return True
            filename = os.path.basename(abs_path)
            return not fnmatch(filename, file_mask)

        _dirs, files = scan_directory(
            path=dir_to_scan,
            recursive=True,
            is_ignored_dir=self.project.is_ignored_path,
            is_ignored_file=is_ignored_file,
            relative_to=self.get_project_root(),
        )
        return self._to_json({"files": files})


class ReplaceContentTool(Tool, ToolMarkerCanEdit):
    """Replace content in file."""

    def apply(
        self,
        relative_path: str,
        needle: str,
        repl: str,
        mode: Literal["literal", "regex"],
        allow_multiple_occurrences: bool = False,
    ) -> str:
        """Replace pattern in file."""
        return self.replace_content(
            relative_path, needle, repl, mode=mode, allow_multiple_occurrences=allow_multiple_occurrences, require_not_ignored=True
        )

    @staticmethod
    def _create_replacement_function(regex_pattern: str, repl_template: str, regex_flags: int) -> Callable[[re.Match], str]:
        def validate_and_replace(match: re.Match) -> str:
            matched_text = match.group(0)
            if "\n" in matched_text and re.search(regex_pattern, matched_text[1:], flags=regex_flags):
                raise ValueError("Match is ambiguous.")
            def expand_backreference(m: re.Match) -> str:
                group_num = int(m.group(1))
                group_value = match.group(group_num)
                return group_value if group_value is not None else m.group(0)
            result = re.sub(r"\$!(\d+)", expand_backreference, repl_template)
            return result
        return validate_and_replace

    def replace_content(
        self,
        relative_path: str,
        needle: str,
        repl: str,
        mode: Literal["literal", "regex"],
        allow_multiple_occurrences: bool = False,
        require_not_ignored: bool = True,
    ) -> str:
        self.project.validate_relative_path(relative_path, require_not_ignored=require_not_ignored)
        with EditedFileContext(relative_path, self.create_code_editor()) as context:
            original_content = context.get_original_content()
            if mode == "literal":
                regex = re.escape(needle)
            elif mode == "regex":
                regex = needle
            else:
                raise ValueError(f"Invalid mode: '{mode}'")
            regex_flags = re.DOTALL | re.MULTILINE
            repl_fn = self._create_replacement_function(regex, repl, regex_flags=regex_flags)
            updated_content, n = re.subn(regex, repl_fn, original_content, flags=regex_flags)
            if n == 0:
                raise ValueError(f"No matches found in '{relative_path}'.")
            if not allow_multiple_occurrences and n > 1:
                raise ValueError(f"Expression matches {n} occurrences.")
            context.set_updated_content(updated_content)
        return SUCCESS_RESULT


class DeleteLinesTool(Tool, ToolMarkerCanEdit, ToolMarkerOptional):
    """Delete lines in file."""

    def apply(self, relative_path: str, start_line: int, end_line: int) -> str:
        """Delete line range."""
        code_editor = self.create_code_editor()
        code_editor.delete_lines(relative_path, start_line, end_line)
        return SUCCESS_RESULT


class ReplaceLinesTool(Tool, ToolMarkerCanEdit, ToolMarkerOptional):
    """Replace lines in file."""

    def apply(self, relative_path: str, start_line: int, end_line: int, content: str) -> str:
        """Replace line range."""
        if not content.endswith("\n"):
            content += "\n"
        result = self.agent.get_tool(DeleteLinesTool).apply(relative_path, start_line, end_line)
        if result != SUCCESS_RESULT:
            return result
        self.agent.get_tool(InsertAtLineTool).apply(relative_path, start_line, content)
        return SUCCESS_RESULT


class InsertAtLineTool(Tool, ToolMarkerCanEdit, ToolMarkerOptional):
    """Insert at line."""

    def apply(self, relative_path: str, line: int, content: str) -> str:
        """Insert content at line."""
        if not content.endswith("\n"):
            content += "\n"
        code_editor = self.create_code_editor()
        code_editor.insert_at_line(relative_path, line, content)
        return SUCCESS_RESULT


class SearchForPatternTool(Tool):
    """Search pattern in project."""

    def apply(
        self,
        substring_pattern: str,
        context_lines_before: int = 0,
        context_lines_after: int = 0,
        paths_include_glob: str = "",
        paths_exclude_glob: str = "",
        relative_path: str = "",
        restrict_search_to_code_files: bool = False,
        max_answer_chars: int = -1,
    ) -> str:
        """Search for pattern. Prefer symbolic tools for symbols."""
        abs_path = os.path.join(self.get_project_root(), relative_path)
        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"Path {relative_path} does not exist.")

        if restrict_search_to_code_files:
            matches = self.project.search_source_files_for_pattern(
                pattern=substring_pattern,
                relative_path=relative_path,
                context_lines_before=context_lines_before,
                context_lines_after=context_lines_after,
                paths_include_glob=paths_include_glob.strip(),
                paths_exclude_glob=paths_exclude_glob.strip(),
            )
        else:
            if os.path.isfile(abs_path):
                rel_paths_to_search = [relative_path]
            else:
                _dirs, rel_paths_to_search = scan_directory(
                    path=abs_path,
                    recursive=True,
                    is_ignored_dir=self.project.is_ignored_path,
                    is_ignored_file=self.project.is_ignored_path,
                    relative_to=self.get_project_root(),
                )
            matches = search_files(
                rel_paths_to_search,
                substring_pattern,
                file_reader=self.project.read_file,
                root_path=self.get_project_root(),
                paths_include_glob=paths_include_glob,
                paths_exclude_glob=paths_exclude_glob,
            )
        file_to_matches: dict[str, list[str]] = defaultdict(list)
        for match in matches:
            assert match.source_file_path is not None
            file_to_matches[match.source_file_path].append(match.to_display_string())
        result = self._to_json(file_to_matches)
        return self._limit_length(result, max_answer_chars)
