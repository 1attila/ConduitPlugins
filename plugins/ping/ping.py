from typing import Union, List, Optional
from dataclasses import dataclass
import enum
import re

from mconduit import plugins, Context, Event, Player, text


class PingType(enum.Enum):
    Small = enum.auto()
    Big   = enum.auto()


@dataclass
class PingData:
    target: str
    type: PingType
    message: Optional[str]


class PlayerNotFound(Exception):
    ...


class Ping(plugins.Plugin):
    """
    MCDReforged beep equivalent
    """

    def _parse_ping(self, message: str, players: List[str]) -> Optional[List[PingData]]:
        """
        Splits the target player from the rest of the message, if it exists
        """

        pattern = re.compile(r'(@{1,2})\s*([\w-]+)')
        matches = list(pattern.finditer(message))
        
        if not matches:
            return

        results: List[PingData] = []
        i = 0

        for match in matches:

            ping_symbol = match.group(1)
            candidate = match.group(2)

            ping_type = PingType.Small if ping_symbol == "@" else PingType.Big

            group_players = [candidate]
            words = message[match.end():].split(" ")
            words = [word for word in words]
            ping_offset = 0

            for word in words:

                if len(word.replace(" ", "")) == 0:
                    ping_offset += len(word)

                elif word in players:

                    group_players.append(word)
                    ping_offset += len(word) + 1

                else:
                    break

            trailing_message = message[match.end()+ping_offset:]
            
            for p in group_players:
                results.append(PingData(target=p, type=ping_type, message=trailing_message))

        return results
    
    
    def _get_players_name(self) -> List[str]:
        return [p.name for p in self.server.get_online_players()]


    def _get_player(self, player: Union[Player, str]) -> str:
        """
        Finds the target player
        """
        
        if player.lower() in ["all" or "@a"]:
            return "@a"
        
        if isinstance(player, Player):
            return str(player)
        
        if player in self._get_players_name():
            return player
        
        raise PlayerNotFound()


    def small_ping(self, player: Union[Player, str]):
        """
        Emits a small sound at the player location
        """
        
        try:
            target = self._get_player(player)

            self.server.execute(f"/execute at {target} run playsound minecraft:entity.arrow.hit_player player {target}")
        except Exception as e:
            raise e


    def big_ping(self, player: Union[Player, str], requester: Optional[str]=None, message: Optional[str]=None):
        """
        Emits a small sound at the player location and displays the requester with it's message at the given player
        """

        try:
            target = self._get_player(player)

            if requester is None:
                requester = "Someone"

            self.small_ping(target)
            self.server.execute(f"/title {target} times 2 15 5")
            self.server.execute(f"""/title {target} title {text.yellow(requester)}""")

            if message is None:
                message = "Is pinging you!"

            self.server.execute(f"""/title {target} subtitle {text.yellow(message)}""")

        except Exception as e:
            raise e


    @plugins.event(event=Event.PlayerChat)
    def on_player_message(self, ctx: Context):

        if "@" not in ctx.message:
            return

        try:

            online_players = self._get_players_name()
            pings = self._parse_ping(ctx.message, online_players)

            for ping in pings:

                if ping.type == PingType.Big:
                    
                    ping_message = None

                    if ping.message is not None and len(ping.message.replace(" ", "")) > 0:
                        ping_message = ping.message

                    self.big_ping(
                        ping.target,
                        requester=str(ctx.player),
                        message=ping_message
                    )

                else:
                    self.small_ping(ping.target)

        except Exception as e:
            ctx.error(e)