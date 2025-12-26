# List of Tools

Find the full list of Serena's tools below (output of `<serena> tools list --all`).

Note that in most configurations, only a subset of these tools will be enabled simultaneously (see the section on [configuration](../02-usage/050_configuration) for details).

* `activate_project`: Activates a project based on the project name or path.
* `check_onboarding_performed`: Checks whether project onboarding was already performed.
* `delete_lines`: Deletes a range of lines within a file.
* `delete_memory`: Deletes a memory from Serena's project-specific memory store.
* `find_referencing_symbols`: Finds symbols that reference the symbol at the given location (optionally filtered by type).
* `find_symbol`: Performs a global (or local) search for symbols with/containing a given name/substring (optionally filtered by type).
* `get_symbols_overview`: Gets an overview of the top-level symbols defined in a given file.
* `initial_instructions`: Provides instructions on how to use the Serena toolbox.
* `insert_at_line`: Inserts content at a given line in a file.
* `jet_brains_find_referencing_symbols`: Finds symbols that reference the given symbol
* `jet_brains_find_symbol`: Performs a global (or local) search for symbols with/containing a given name/substring (optionally filtered by type).
* `jet_brains_get_symbols_overview`: Retrieves an overview of the top-level symbols within a specified file
* `list_dir`: Lists files and directories in the given directory (optionally with recursion).
* `list_memories`: Lists memories in Serena's project-specific memory store.
* `onboarding`: Performs onboarding (identifying the project structure and essential tasks, e.g. for testing or building).
* `read_memory`: Reads the memory with the given name from Serena's project-specific memory store.
* `remove_project`: Removes a project from the Serena configuration.
* `rename_symbol`: Renames a symbol throughout the codebase using language server refactoring capabilities.
* `replace_lines`: Replaces a range of lines within a file with new content.
* `replace_content`: Replaces content in a file (optionally using regular expressions).
* `restart_language_server`: Restarts the language server, may be necessary when edits not through Serena happen.
* `summarize_changes`: Provides instructions for summarizing the changes made to the codebase.
* `switch_modes`: Activates modes by providing a list of their names
* `think_about_collected_information`: Thinking tool for pondering the completeness of collected information.
* `think_about_task_adherence`: Thinking tool for determining whether the agent is still on track with the current task.
* `think_about_whether_you_are_done`: Thinking tool for determining whether the task is truly completed.
* `write_memory`: Writes a named memory (for future reference) to Serena's project-specific memory store.
