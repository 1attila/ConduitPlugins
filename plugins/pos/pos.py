from typing import Optional

from mconduit import plugins, Context, text, Dimension, Player, Color, Gamemode


class Pos(plugins.Plugin):
    """
    Displays player position
    """


    @plugins.command
    def pos(self, ctx: Context, player_name: Optional[str]=None):
        
        player: Player = None

        if player_name is not None:
            player = ctx.server.get_player_by_name(player_name)
        else:
            player = ctx.player
        
        if player is None:
            ctx.reply(text.red(f"Player '{player_name}' is not online!"))
        
        dim_color = {
            Dimension.Overworld: Color.Green,
            Dimension.Nether:    Color.DarkRed,
            Dimension.End:       Color.Yellow
        }[player.dimension]

        coords_color = {
            Dimension.Overworld: Color.Blue,
            Dimension.Nether:    Color.Red,
            Dimension.End:       Color.Gold
        }[player.dimension]
        
        text_pos = text.Text(player.pos.round(1), color=coords_color)
        
        if ctx.player.gamemode in [Gamemode.Creative, Gamemode.Spectator]:
            text_pos.hover(show_text="Click to teleport").click(
                run_command=f"/execute in {player.dimension.value} run tp {player.name} {player.pos.round(1)}"
            )
        
        msg = text.Text(ctx.player.name), text.Text(" is at ").aqua(), text_pos + text.Text(" in ").aqua(), text.Text(player.dimension.value, color=dim_color)

        if player_name is None:
            
            ctx.say(msg)
        else:
            ctx.reply(msg)

        ctx.server.execute(f"/effect give {player} minecraft:glowing 15 0 true")