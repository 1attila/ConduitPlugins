"""
Quick script to automatically update the /plugins folder.

This should run only on Conduit owner machine
"""


from typing import Optional, Tuple, List
from dataclasses import dataclass, field
import prompt_toolkit.shortcuts
from pathlib import Path
import hashlib
import shutil
import parse
import enum
import json


CONFIG_FILENAME = "config.json"
METADATA_FILENAME = "metadata.json"
FILE_FILTER = [CONFIG_FILENAME]


class UpdateType(enum.Enum):
    NewPlugin  = enum.auto()
    Regular    = enum.auto()
    HashChange = enum.auto()


@dataclass
class PluginUpdate:
    type: UpdateType
    name: str
    current_version: Optional[str] = field(default=None)
    new_version: Optional[str] = field(default=None)


def load_catalogue_path() -> str:
    
    with open(CONFIG_FILENAME, "r") as f:
        return json.load(f)["catalogue_path"]
    

def hash_file(path: Path) -> str:

    h = hashlib.sha256()

    with open(path, "rb") as f:

        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)

    return h.hexdigest()


def hash_folder(folder: Path) -> str:

    hashes = []
    
    for item in folder.iterdir():
        
        if item.is_dir():
            
            if item.name != "__pycache__" and not (item / "persistent.json").exists():
                hashes.append(hash_folder(item))

        elif item.name not in FILE_FILTER:
            hashes.append(hash_file(item))

    return hashlib.sha256("".join(hashes).encode()).hexdigest()


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
            elif hash_folder(file) != hash_folder(Path.cwd() / "plugins" / file.name):
                
                p = parse.parse(r"{stable}.{major}.{minor}", version)

                if p is None:
                    return

                stable, major, minor = p["stable"], p["major"], str(int(p["minor"]) + 1)

                updates.append(
                    PluginUpdate(
                        type=UpdateType.HashChange,
                        name=file.name,
                        current_version=version,
                        new_version=".".join([stable, major, minor])
                    )
                )

    return updates
        

def check_updates(updates: List[PluginUpdate]) -> Tuple[List[str], List[List[str]]]:

    final_updates = []
    new_plugins = []
    plugin_updates = []
    hash_updates = []

    new_plugin_values = [(u.name, u.name) for u in updates if u.type == UpdateType.NewPlugin]
    plugin_updates_values = [(u.name, u.name) for u in updates if u.type == UpdateType.Regular]
    hash_updates_values = [((u.name, u.new_version), f"{u.name} ({u.current_version} -> {u.new_version})") for u in updates if u.type == UpdateType.HashChange]

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

    if len(hash_updates_values) > 0:

        hash_updates = prompt_toolkit.shortcuts.checkboxlist_dialog(
            title="PLUGINS CHANGED",
            text="Update version to plugins",
            values=hash_updates_values
        ).run()

    if new_plugins is not None:
        final_updates.extend(new_plugins)

    if plugin_updates is not None:
        final_updates.extend(plugin_updates)

    if hash_updates is None:
        hash_updates = []

    return final_updates, hash_updates


def update_version(input_dir: Path, new_version: str) -> None:
    
    with open(input_dir / METADATA_FILENAME, "r") as f:
        metadata = json.load(f)
        metadata["version"] = new_version
    
    new_metadata = json.dumps(metadata, indent=4)

    with open(input_dir / METADATA_FILENAME, "w") as f:
        f.write(new_metadata)


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
    plugins_to_update, change_version = check_updates(updates)

    for plugin in change_version:
        update_version(catalogue_path / plugin[0], plugin[1])
        copy_plugin(catalogue_path / plugin[0], Path.cwd() / "plugins" / plugin[0])

    for plugin in plugins_to_update:
        copy_plugin(catalogue_path / plugin, Path.cwd() / "plugins" / plugin)


if __name__ == "__main__":
    main()