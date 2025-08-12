from typing import List

from mconduit import plugins, text, Context, Event


class Config(plugins.Config):
    prefixes: List[str] = ["r"]


class FreeCam(plugins.Plugin[Config]):
    """
    Equivalent to /cs
    """


    def __init__(self, metadata, manager, lang) -> "FreeCam":
        
        super().__init__(metadata, manager, lang)

        try:
            self.persistent.players
        except Exception as e:
            self.persistent.players = {}

    
    @plugins.event(event=Event.PlayerChat)
    def on_player_message(self, ctx: Context):

        if ctx.message.strip().lower() in self.config.prefixes:

            player = ctx.player
            
            if player.name in self.persistent.players.keys():

                gamemode, dim, x, y, z, yaw, pitch = self.persistent.players[player.name]

                self.server.execute(f"/execute in {dim} run tp {player.name} {x} {y} {z} {yaw} {pitch}")
                self.server.execute(f"/gamemode {gamemode} {player.name}")

                msg = text.aqua(f"You have been put into {gamemode}")
                self.server.execute(f"/title {player.name} actionbar {msg}")

                self.persistent.players.pop(player.name)
                self.persistent._save()

            else:
                self.persistent.players[player.name] = (
                    player.gamemode.value,
                    player.dimension.value,
                    *player.pos.as_tuple(),
                    *player.rotation.as_tuple()
                )

                self.persistent._save()

                self.server.execute(f"/gamemode spectator {player.name}")

                ctx.reply(text.aqua("[FreeCam] Click here to back").hover(
                    show_text=str(player.pos.round(1))).click(
                    run_command=f"/execute if entity @a[name={player.name}, gamemode=spectator] run execute in {player.dimension.value} run tp {player.name} {player.pos}")
                )

                msg = text.aqua("You have been put into spectator")
                self.server.execute(f"/title {player.name} actionbar {msg}")