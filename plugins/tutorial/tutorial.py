from typing import Optional, Union, Dict, Tuple, Callable, Any

from mconduit import plugins, text, utils, Context, Event

from .builtin_tutorial import (
    commands,
    commands_with_single_parameter,
    help,
    group_commands
)


TUTORIALS = {
    "commands": commands,
    "commands with a single parameter": commands_with_single_parameter,
    "help command": help,
    "group commands": group_commands
}


class Persistent(plugins.Persistent):
    players: dict[str, dict[str, Union[list[str]]], bool] = {}


class Tutorial(plugins.Plugin[None, Persistent]):
    """
    Explains how to use conduit and its plugins
    """

    
    # TUTORIALS: List[Callable[["Tutorial", str], bool]] = [
    #     "Commands (!!version)",
    #     "Commands with a single parameter (!!news | !!perms)"
    #     "!! help",
    #     "!! group command",
    #     "!! (command cache)",
    #     "Command completion",
    #     "Multiple arguments",
    #     "Multiwords with quotes",
    #     "Variadic arguments",
    #     "Flags",
    #     "Conduit types",
    #     "Permissions",
    #     "Chat interactions",
    #     "Exceptions",
    #     "BuiltinPlugin"
    # ] 


    tutorial = plugins.Command.group(
        name="tutorial",
        aliases=["tut"]
    )


    def on_load(self):
        
        setattr(self, "tutorials", {})

        self.tutorials: Dict[str, Dict[str, Callable[[Context, str], Any]]] = {
            "basic functionalities": TUTORIALS
        }
        
        self._check_players()

    
    def _check_players(self):

        for player in self.server.get_online_players():
            self._check_player(player.name)
    

    @plugins.event(event=Event.PlayerJoin)
    def on_player_join(self, ctx: Context):
        self._check_player(ctx.player.name)

    
    def register_plugin_tutorials(self, 
                                 tutorials: Dict[str, Callable[[plugins.Plugin, str], Any]],
                                 plugin_name: str
                                ) -> None:
        """
        Registers the tutorials for the given plugin name

        :param tutorials: Dict of tutorial-name -> function.
        The function must accept only the plugin instance and player name 

        :param plugin_name: Name of the plugin to link the tutorial. You should put self.name but nothing stops you from using something else
        """
        
        if plugin_name in self.tutorials:
            raise RuntimeError("Plugin name is already used! Please choose another name")
        
        self.tutorials[plugin_name] = tutorials
        self._check_players()

    
    def _get_missing_tutorial_for(self, player: str) -> Optional[Tuple[str, str]]:

        for plg_name, p_tuts in self.tutorials.items():
            
            if plg_name not in self.persistent.players[player]:

                t_name: str
                for n in p_tuts:
                    t_name = n
                    break

                return plg_name, t_name

            for tut in p_tuts.keys():
                
                if tut not in self.persistent.players[player][plg_name]:
                    return plg_name, tut


    def _check_player(self, player):

        if player not in self.persistent.players:
            self._ask_for_tutorial(player, "basic functionalities", "commands", True)
            return

        if self.persistent.players[player].get("notify", True) is True:
            
            missing_tutorial = self._get_missing_tutorial_for(player)

            if missing_tutorial is None:
                return
            
            plugin, tutorial = missing_tutorial
            self._ask_for_tutorial(player, plugin, tutorial, False)

    
    def _set_player_notification(self, player: str, notify: bool):
        """
        Sets the player notification value
        """
        
        self.persistent.players.setdefault(player, {})
        self.persistent.players[player]["notify"] = notify


    def _get_ask_message(self,
                         player: str,
                         plugin: str,
                         tutorial: str
                        ) -> text.Text:
        """
        Generates the text to choose the options
        """

        yes = text.green("[YES]").underlined().bold()
        yes.hover("Click to start/continue the tutorial")
        yes.click(run_function=lambda c: self._start_tutorial(player, plugin, tutorial))

        later = text.aqua("[LATER]").underlined()
        later.hover("Click to ask when you join next time")
        later.click(run_function= lambda c: self._set_player_notification(player, True))

        no = text.red("[DONT ASK AGAIN]").underlined()
        no.hover("Click to dont get this notification again")
        no.click(run_function=lambda c: self._set_player_notification(player, False))

        return yes + " " + later + " " + no


    def _ask_for_tutorial(self,
                          player: str,
                          plugin: str,
                          tutorial: str,
                          first_time: bool=True
                        ):
        
        if first_time is True:

            initial_msg = text.yellow(f"Hello {player}! This server uses ")

            conduit_msg = text.dark_aqua("Conduit").underlined().bold()
            conduit_msg.hover("Click to go to the GitHub page!")
            conduit_msg.click(open_url="https://github.com/1attila/Conduit")

            initial_msg += conduit_msg
            initial_msg += text.yellow(", a plugin system for Minecraft!\n")
            initial_msg += text.yellow("Would you like to get a short tutorial on how to use it?")

        else:
            initial_msg = text.yellow(f"Hello {player}! Conduit has new features you should be aware of!\n")
            initial_msg += text.yellow("Would you like to get a short update?")

        self.server.tellraw(player, initial_msg)
        self.server.tellraw(player, self._get_ask_message(player, plugin, tutorial))


    def _confirm_ask_next(self, player: str) -> text.Text:
        
        more_tutorials = self._get_missing_tutorial_for(player)

        advert = text.aqua("Tutorial completed!")

        if more_tutorials is None:
            return advert

        plugin_name, next_tutorial = more_tutorials

        question = text.aqua("Want to start next tutorial? ")

        yes = text.green("[YES]").underlined().bold()
        yes.hover(show_text="Click to start a next tutorial")
        yes.click(run_function=lambda c: self._start_tutorial(player, plugin_name, next_tutorial))

        question += yes

        advert += " "
        advert += question 

        return advert

    
    def _start_tutorial(self, player: str, plugin_name: str, tutorial_name: str):
        """
        Runs all the tutorial the player didnt do, unless player ask to stop
        """
        
        self._set_player_notification(player, True)

        if plugin_name not in self.tutorials:
            self.server.tellraw(player, text.red("Invalid tutorial"))
            return
        
        if tutorial_name not in self.tutorials[plugin_name]:
            self.server.tellraw(player, text.red("Invalid tutorial"))
            return

        try:
            tutorial = self.tutorials[plugin_name][tutorial_name]

            tutorial(self, player)

            self.persistent.players[player].setdefault(plugin_name, [])\
            .append(tutorial_name)
            
            self.server.tellraw(player, self._confirm_ask_next(player))

        except Exception as e:
            
            self.server.tellraw(player, utils.ConduitError.from_exception(e).to_text())
    

    @tutorial.command
    def start(self, ctx: Context, plugin: str, name: str):
        """
        Starts the given tutorial
        """

        self._start_tutorial(ctx.player.name, plugin, name)
    

    @tutorial.command
    def list(self, ctx: Context, plugin: str="basic functionalities"):
        """
        Lists the missing tutorials for the given plugin
        """

        if plugin not in self.tutorials:
            ctx.error("There is no plugin named " + text.quoted(plugin).red())
            return

        msg = text.dark_aqua("Tutorials: ").bold().endl()

        for tutorial in self.tutorials[plugin].keys():

            msg += text.aqua(tutorial) + " "
            msg += text.button(
                text.icon.play,
                sound="entity.arrow.hit_player",
                show_text="Click to start this tutorial",
                run_function=lambda c: self._start_tutorial(c.player.name, plugin, tutorial)
            ).green()
            msg += " "
            
            if ctx.player.name not in self.persistent.players:
                self.persistent.players.get(ctx.player.name, {})

            if plugin not in self.persistent.players[ctx.player.name]:
                self.persistent.players[ctx.player.name].get(plugin, [])

            if tutorial in self.persistent.players[ctx.player.name][plugin]:

                msg += text.button(
                    text.icon.x,
                    sound="block.note_block.bass",
                    show_text="Remove from completed tutorials",
                    run_function=lambda c: self.persistent.players[ctx.player.name][plugin].remove(tutorial)
                ).red()

            else:
                msg += text.button(
                    text.icon.plus,
                    sound="block.note_block.pling",
                    show_text="Mark as completed",
                    run_function=lambda c: self.persistent.players[ctx.player.name][plugin].append(tutorial)
                ).gold()

            msg.endl()

        ctx.reply(msg)