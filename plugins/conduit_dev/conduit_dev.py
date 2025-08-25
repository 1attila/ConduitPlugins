from typing import Callable, NoReturn, Optional
from pathlib import Path
import json
import os

from watchdog.observers import Observer
from watchdog.events import DirModifiedEvent, FileModifiedEvent, FileSystemEventHandler
from mconduit import plugins, Context, text, constants


class Config(plugins.Config):
    github_api_url: str = ""
    enable_reload: bool = False


class ReloadHandler(FileSystemEventHandler):
    """
    Detects when a Plugin changes and reloads it
    """

    __callback: Callable


    def __init__(self, callback: Callable) -> NoReturn:
        
        self.__callback = callback


    def on_modified(self, event: DirModifiedEvent | FileModifiedEvent) -> NoReturn:

        if type(event) is FileModifiedEvent:

            if not event.src_path.endswith(".py"):
                return
            
            if event.src_path.__contains__("__pycache__"):
                return
            
            changed_path = Path(event.src_path).resolve()
            current = changed_path
            plugins_root = Path(constants.PLUGINS_DIR).resolve()

            while current != plugins_root and plugins_root in current.parents:

                metadata_file = current / constants.METADATA_FILENAME

                if metadata_file.exists():

                    try:
                        with metadata_file.open("r", encoding="utf-8") as f:

                            metadata = json.load(f)
                            plugin_name = metadata.get("name")

                            if plugin_name != "conduit_dev":

                                self.__callback(plugin_name)

                            return
                        
                    except Exception as e:
                        return

                current = current.parent


class ConduitDev(plugins.Plugin[Config]):
    """
    Utilities for Conduit Devs & plugin development
    """

    cdev = plugins.Command.group("cdev", aliases=["cd"])
    __observer: Observer
    __reloader: ReloadHandler


    def __init__(self, manager, metadata, lang) -> "ConduitDev":

        super().__init__(manager, metadata, lang)

        self.__reloader = ReloadHandler(self._reload_plugin)
        self.__observer = Observer()
        self.__observer.schedule(self.__reloader, path=constants.PLUGINS_DIR, recursive=True)
        self.__observer.start()

    
    def _reload_plugin(self, plugin_name: str) -> NoReturn:
        """
        Reloads the plugin with the given name and let the user know, if the `enable_reload` is set to `True`
        """

        if not self.config.enable_reload:
            return
        
        try:
            self.manager.reload_plugin(plugin_name)

            msg = text.green("Plugin") + text.green(f" `{plugin_name}` ").hover(
                show_text=self.manager.get_plugin_named(plugin_name).desc
                ) + "has been reloaded sucesfully!"
            
            self.server.execute(f"/tellraw @a {msg}")

        except Exception as e:
            
            if type(e).__name__ == "PluginNotLoaded":
                return

            err = text.red(type(e).__name__)
            self.server.execute(f"/tellraw @a {err}")
    

    @cdev.command
    def download(self, ctx: Context, plugin_name: str, repo: str=""):
        """
        Download a plugin from the specified GitHub repo.
        """

        repo = repo if len(repo) > 0 else self.config.github_api_url

        try:
            self.manager._download_plugin(plugin_name, repo)

            ctx.reply(
                text.green("Plugin") + text.green(f" `{plugin_name}` ").hover(
                show_text=self.manager.get_plugin_named(plugin_name).desc
                ) + "has been downloaded sucesfully!"
            )
            
        except Exception as e:
            ctx.error(e)


    @cdev.command
    def update(self, ctx: Context, plugin_name: str, repo: str=""):
        """
        Updates a plugin from the specified GitHub repo.

        This command gives a lot more freedom compared to `!!plugin update`, as it doesn't do any check
        """

        repo = repo if len(repo) > 0 else self.__git_url

        try:
            self.manager._download_plugin(plugin_name, repo)

            ctx.reply(text.green(f"Plugin `{plugin_name}` has been updated sucesfully!").hover(
                show_text="Click here to reload").click(
                suggest_command=f"!! plugin reload {plugin_name}")
            )

        except Exception as e:
            ctx.error(e)


    def _lower_to_camel_case(self, camel: str) -> str:
        """
        Converts a lower-case string into a snake-case one.

        E.g: 'hello_world' -> 'HelloWorld'
        """

        out = ""
        upper_flag = False

        for i, item in enumerate(camel.strip()):
            

            if upper_flag is True or i == 0:

                upper_flag = False
                out += item.upper()
            else:
                out += item

            if item == "_":
                upper_flag = True
                out = out.removesuffix("_")

        return out

    
    @cdev.command
    def generate(self, ctx: Context,
                 name: str,
                 description: str="",
                 entrypoint: Optional[str]=None):
        """
        Setups a new plugin in `plugins`
        """

        path = Path(constants.PLUGINS_DIR).joinpath(name)

        if path.exists():
            ctx.error("A plugin with that name is already installed!")

        # TODO: Check for plugins in the PluginCatalogue

        if entrypoint is None:
            entrypoint = name

        if not entrypoint.endswith(".py"):
            entrypoint += ".py"

        os.makedirs(path, exist_ok=True)
        
        with open(os.path.join(path, "metadata.json"), "x") as f:
            
            metadata = {   
                "name": name,
                "authors": [ctx.player.name],
                "url": "",
                "documentation": "",
                "entrypoint": entrypoint,
                "required_plugins": [],
                "version": "0.0.0",
                "description": description,
                "dependencies": [],
                "python_version": "",
                "supported_langs": ["en_us"]
            }

            f.write(json.dumps(metadata, indent=4))

        with open(os.path.join(path, entrypoint), "x") as f:
            
            plugin_class_name = self._lower_to_camel_case(entrypoint.removesuffix(".py"))

            f.write(
                f"from mconduit import plugins\n\n\nclass {plugin_class_name}(plugins.Plugin):\n    ..."
            )

        ctx.success("Project structure generated sucesfully!")

    
    def about_to_stop(self) -> NoReturn:
        
        self.__observer.stop()
        self.__observer.join()