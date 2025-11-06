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
            return
        
        dim_color = {
            Dimension.Overworld: Color.DarkGreen,
            Dimension.Nether:    Color.DarkRed,
            Dimension.End:       Color.Gold
        }[player.dimension]

        coords_color = {
            Dimension.Overworld: Color.Green,
            Dimension.Nether:    Color.Red,
            Dimension.End:       Color.Yellow
        }[player.dimension]
        
        text_pos = text.Text(player.pos.round(1), color=coords_color)
        
        
        text_pos.hover(show_text="Click to teleport")
        text_pos.click(
            run_command=f"/execute if entity @a[name={ctx.player.name}, gamemode=spectator] run execute in {player.dimension.value} run tp {player.name} {player.pos.round(1)}"
        ) # TODO: Replace with run_function=
        
        msg = text.gray(player_name)
        msg += text.aqua(" is at ") 
        msg += text_pos + text.aqua(" in ")
        msg += text.Text(player.dimension.value, color=dim_color)
        
        if player_name is None:
            
            ctx.say(msg)
        else:
            ctx.reply(msg)

        ctx.server.execute(f"/effect give {player} minecraft:glowing 15 0 true")