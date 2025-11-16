from collections import defaultdict
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import List

from controller.controller_inputs import ControllerInput

from display.display import Display
from utils.logger import PyUiLogger
from views.grid_or_list_entry import GridOrListEntry
from views.selection import Selection
from views.view_creator import ViewCreator
from views.view_type import ViewType

"""
Refactored OptionSelectUI - static class

Behavior notes:
- Fully static class (no instances needed).
- All methods take explicit parameters; no closure over exit_after_running.
- get_top_level_options(...) returns a list of GridOrListEntry where each
  entry.value is a lambda that, when called, runs the original action
  preserving the original behavior for exit_after_running.
- display_menu_ui(...) shows the UI and behaves like the original function.
- display_option_list(...) remains a convenience entrypoint that reads the
  JSON file and either displays the UI or returns the top-level options.
"""

class OptionSelectUI:
    @staticmethod
    def _build_tree_from_flat_map(flat_map):
        """
        Convert a flat dict with slash-separated keys into a nested dict-of-dicts.
        Leaves (final parts) contain the original string value.
        """
        def tree():
            return defaultdict(tree)
        root = tree()

        for key, value in flat_map.items():
            parts = key.split("/")
            node = root
            for part in parts[:-1]:
                node = node[part]
            node[parts[-1]] = value  # leaf = original path/string
        return root

    @staticmethod
    def _write_result_to_file(result):
        """Write selection result to selection.txt next to package root (two levels up)."""
        script_dir = Path(__file__).resolve().parent.parent
        result_file = script_dir / "selection.txt"
        PyUiLogger.get_logger().info(f"Writing {result} to {result_file}")
        try:
            with result_file.open("w", encoding="utf-8") as f:
                f.write(result)
        except Exception as e:
            PyUiLogger.get_logger().error(f"Error writing result to file: {e}")

    @staticmethod
    def _make_option_list_from_menu(menu_dict, folder, is_root, exit_after_running, execute_immediately=False):
        def run_action(val):
            """Perform the final action exactly as original behavior required."""
            if exit_after_running:
                Display.deinit_display()
                subprocess.run(val, shell=True)
                sys.exit(0)
            elif execute_immediately:
                Display.display_message(f"Executing: {val}")
                subprocess.run(val, shell=True)                        
                Display.display_message(f"Finished Running {val}", duration_ms=2000)
                return val
            else:
                OptionSelectUI._write_result_to_file(val)
                return val

        option_list = []

        for key, val in menu_dict.items():
            img_path = f"{folder}/Imgs/{key}.png"
            if not os.path.exists(img_path):
                img_path = f"{folder}/Imgs/{key}.qoi"

            if is_root:
                if isinstance(val, str):
                    # leaf node
                    option_value = lambda _ignored_controller_input=None, v=val: run_action(v)
                else:
                    # submenu node
                    option_value = lambda _ignored_controller_input=None, v=val, k=key, execute_immediately=execute_immediately: OptionSelectUI.navigate_menu(
                        v, k, folder, exit_after_running, is_root=False, execute_immediately=execute_immediately
                    )
            else:
                # normal navigation mode (UI) just store key
                option_value = key

            option_list.append(
                GridOrListEntry(
                    primary_text=key,
                    value=option_value,
                    image_path=img_path
                )
            )

        return option_list


    @staticmethod
    def navigate_menu(menu_dict, title, folder, exit_after_running, execute_immediately=False, is_root=False):
        """
        Core navigation function.

        - If is_root is True: returns the built top-level option_list where each
          entry.value is a callable that will perform the final action when invoked.
        - If is_root is False: launches the UI for the provided menu_dict and handles
          navigation (this is the same behavior as the original navigate_menu).
        """
        # Build option_list (lambdas only if is_root=True)
        option_list = OptionSelectUI._make_option_list_from_menu(
            menu_dict, folder, is_root, exit_after_running, execute_immediately=execute_immediately
        )

        # If top-level mode requested, return the built options instead of showing UI
        if is_root:
            return option_list

        # Otherwise show UI and perform navigation exactly like original
        selected = Selection(None, None, 0)
        view = ViewCreator.create_view(
            view_type=ViewType.TEXT_AND_IMAGE,
            top_bar_text=title,
            options=option_list,
            selected_index=selected.get_index()
        )

        while True:
            selected = view.get_selection([ControllerInput.A, ControllerInput.B])
            if selected is None:
                continue

            inp = selected.get_input()
            entry = selected.get_selection()

            if inp == ControllerInput.B:
                # In submenu/UI flow, B goes up one level (return None to indicate "go up")
                return None

            elif inp == ControllerInput.A:
                # entry.get_value() returns the key for non-root UI builds
                key = entry.get_value()
                # Lookup the corresponding value from the original menu_dict
                val = menu_dict[key]

                if isinstance(val, str):
                    # Final executable task
                    if exit_after_running:
                        Display.deinit_display()
                        subprocess.run(val, shell=True)
                        sys.exit(0)
                    elif execute_immediately:
                        Display.display_message(f"Executing: {val}")
                        subprocess.run(val, shell=True)                        
                        Display.display_message(f"Finished Running {val}", duration_ms=1000)
                        return val                          
                    else:
                        OptionSelectUI._write_result_to_file(val)
                        return val
                else:
                    # Submenu: open and navigate recursively
                    result = OptionSelectUI.navigate_menu(
                        val, key, folder, exit_after_running,execute_immediately=execute_immediately, is_root=False
                    )
                    if result is not None:
                        return result
                    # else, we backed out of the submenu — continue loop

    @staticmethod
    def get_top_level_options(title, root, folder, exit_after_running):
        """
        Legacy wrapper. Preserves old signature so no callers break.
        `title` is ignored because this function now only returns the list.
        """
        root_path = Path(root) / folder
        return OptionSelectUI._build_top_level_options(root_path)

    @staticmethod
    def get_top_level_options_from_json(json_path: str | Path, exit_after_running=False, execute_immediately=False) -> List[GridOrListEntry]:
        """
        New preferred interface. Accepts a path to a JSON file.
        Returns a list of GridOrListEntry where each .value is a lambda
        that will perform the original final action when called.
        """
        json_path = Path(json_path)
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        root_dict = OptionSelectUI._build_tree_from_flat_map(data)
        folder = str(json_path.parent)
        return OptionSelectUI.navigate_menu(root_dict, "", folder, exit_after_running, execute_immediately=execute_immediately, is_root=True)

    @staticmethod
    def display_menu_ui(title, menu_dict, folder, exit_after_running):
        """
        Display the menu UI starting from the provided menu_dict (typically the root).
        Behaves like the original implementation (shows UI, handles navigation,
        executes commands or writes results depending on exit_after_running).
        """
        return OptionSelectUI.navigate_menu(
            menu_dict, title, folder, exit_after_running, is_root=False
        )

    #
    # Convenience entrypoint that mirrors the original public API:
    # display_option_list(title, input_json, exit_after_running)
    #
    @staticmethod
    def display_option_list(title, input_json, exit_after_running):
        """
        Read the JSON file, build the nested menu structure, and either:
         - display the UI (if you call the method that does the UI), or
         - return the top-level options via get_top_level_options(...) if you prefer.

        This convenience method keeps the original signature and behavior when the
        caller wants the UI displayed directly (we call display_menu_ui).
        """
        # --- Load JSON file ---
        with open(input_json, "r", encoding="utf-8") as f:
            data = json.load(f)

        # --- Convert flat paths into nested dict ---
        root = OptionSelectUI._build_tree_from_flat_map(data)

        folder = str(Path(input_json).parent)

        # By default we preserve original behavior: display the UI at root
        result = OptionSelectUI.display_menu_ui(title, root, folder, exit_after_running)
        if(result is None):
            OptionSelectUI._write_result_to_file("EXIT")
            result = "EXIT"

        return result