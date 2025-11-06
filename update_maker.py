"""
Quick script to automatically update the /plugins folder.

This should run only on Conduit owner machine
"""


from typing import List
from dataclasses import dataclass
import prompt_toolkit.completion
import prompt_toolkit.shortcuts
from pathlib import Path
import enum
import json
import os


CONFIG_FILENAME = "config.json"
METADATA_FILENAME = "metadata.json"


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

            if not (Path(os.getcwd()) / file.name).exists():
                updates.append(
                    PluginUpdate(
                        type=UpdateType.NewPlugin,
                        name=file.name
                    )
                )
                continue
            
            with open(file / METADATA_FILENAME, "r") as f:
                version = json.load(f)["version"]

            with open(Path(os.getcwd()) / file.name, "r") as f:
                c_version = json.load(f)["version"]

            if version != c_version:
                updates.append(
                    PluginUpdate(
                        type=UpdateType.Regular,
                        name=file.name
                    )
                )

    return updates
        

def check_updates(updates: List[PluginUpdate]) -> List[PluginUpdate]:

    final_updates = []
    sess = prompt_toolkit.shortcuts.PromptSession

    print("New plugins:")

    for u in updates:

        if u.type == UpdateType.NewPlugin:
            a = sess.prompt(f" * {u.name}")
    
    print("Updates: ")

    for u in updates:

        if u.type == UpdateType.Regular:
            a = sess.prompt(f" * {u.name}")

    return final_updates


def main() -> None:
    
    catalogue_path = load_catalogue_path()

    updates = get_plugins(catalogue_path)

    completer = prompt_toolkit.completion.NestedCompleter(
        {

        }
    )

    while True:
        ...



if __name__ == "__main__":
    main()