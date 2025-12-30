"""
Quick script to automatically update the /plugins folder.

This should run only on Conduit owner machine
"""


from typing import List
from dataclasses import dataclass
import prompt_toolkit.completion
import prompt_toolkit.shortcuts
from prompt_toolkit.styles import Style
from pathlib import Path
import shutil
import enum
import json
import os


CONFIG_FILENAME = "config.json"
METADATA_FILENAME = "metadata.json"
FILE_FILTER = [CONFIG_FILENAME]


class UpdateType(enum.Enum):
    NewPlugin = enum.auto()
    Regular   = enum.auto()


@dataclass
class PluginUpdate:
    type: UpdateType
    name: str


def load_catalogue_path() -> str:
    
    with open(CONFIG_FILENAME, "r") as f:
        return json.load(f)["catalogue_path"]
    

def get_plugins(catalogue_path: Path) -> List[PluginUpdate]:

    updates = []

    for file in catalogue_path.iterdir():

        if (file / METADATA_FILENAME).exists():

            if (
                not (Path.cwd() / "plugins" / file.name).exists() or
                not (Path.cwd() / "plugins" / file.name / METADATA_FILENAME).exists()
                ):

                updates.append(
                    PluginUpdate(
                        type=UpdateType.NewPlugin,
                        name=file.name
                    )
                )
                continue

            with open(catalogue_path / file / METADATA_FILENAME, "r") as f:
                version = json.load(f)["version"]

            #TODO: add metadata checks
            with open(Path.cwd() / "plugins" / file.name / METADATA_FILENAME, "r") as f:

                metadata = json.load(f)
                c_version = metadata["version"]
            
            if version != c_version:

                updates.append(
                    PluginUpdate(
                        type=UpdateType.Regular,
                        name=file.name
                    )
                )

    return updates
        

def check_updates(updates: List[PluginUpdate]) -> List[str]:

    final_updates = []
    new_plugins = []
    plugin_updates = []

    new_plugin_values = [(u.name, u.name) for u in updates if u.type == UpdateType.NewPlugin]
    plugin_updates_values = [(u.name, u.name) for u in updates if u.type == UpdateType.Regular]

    if len(new_plugin_values) > 0:

        new_plugins = prompt_toolkit.shortcuts.checkboxlist_dialog(
            title="NEW PLUGINS",
            text="New plugins to push to the catalogue",
            values=new_plugin_values,
        ).run()

    if len(plugin_updates_values) > 0:
        
        plugin_updates = prompt_toolkit.shortcuts.checkboxlist_dialog(
            title="UPDATED PLUGINS",
            text="Updates to push to the catalogue",
            values=plugin_updates_values
        ).run()

    if new_plugins is not None:
        final_updates.extend(new_plugins)

    if plugin_updates is not None:
        final_updates.extend(plugin_updates)

    return final_updates


def copy_plugin(input_dir: Path, output_dir: Path) -> None:
    
    output_dir.mkdir(parents=True, exist_ok=True)

    for item in input_dir.iterdir():

        if item.is_dir():
            
            if item.name != "__pycache__" and not (item / "persistent.json").exists():
                shutil.copytree(item, output_dir / item.name, dirs_exist_ok=True)

        elif item.name not in FILE_FILTER:
            shutil.copy2(item, output_dir / item.name)


def main() -> None:
    
    catalogue_path = Path(load_catalogue_path())

    updates = get_plugins(catalogue_path)
    plugins_to_update = check_updates(updates)

    for plugin in plugins_to_update:
        copy_plugin(catalogue_path / plugin, Path.cwd() / "plugins" / plugin)


if __name__ == "__main__":
    main()