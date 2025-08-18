from typing import Union, Optional

from mconduit import plugins, Context, Event, Player, text


class PlayerNotFound(Exception):
    ...


class Ping(plugins.Plugin):
    """
    MCDReforged beep equivalent
    """
    

    def _get_player(self, player: Union[Player, str]) -> str:

        if player == "all":
            return "@a"
        
        if isinstance(player, Player):
            return str(player)
        
        if player in [p.name for p in self.server.get_online_players()]:
            return player

        raise PlayerNotFound()


    def small_ping(self, player: Union[Player, str]):
        
        try:
            target = self._get_player(player)

            self.server.execute(f"/execute at {target} run playsound minecraft:entity.arrow.hit_player player {target}")
        except Exception as e:
            raise e


    def big_ping(self, player: Union[Player, str], requester: Optional[str]=None):

        try:
            target = self._get_player(player)

            if requester is None:
                requester = "Someone"

            self.small_ping(target)
            self.server.execute(f"/title {target} times 2 15 5")
            self.server.execute(f"""/title {target} title {text.yellow(requester)}""")
            self.server.execute(f"""/title {target} subtitle {text.yellow("Is pinging you!")}""")

        except Exception as e:
            raise e


    @plugins.event(event=Event.PlayerChat)
    def on_player_message(self, ctx: Context):
        
        ping_type = ctx.message.strip()

        try:
            if ping_type.startswith("@@"):
            
                self.big_ping(ping_type.replace("@@", "").strip(), requester=str(ctx.player))

            elif ping_type.startswith("@"):
            
                self.small_ping(ping_type.replace("@", "").strip())

        except Exception as e:
            ctx.error(e)