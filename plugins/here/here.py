from typing import Optional

from mconduit import plugins, Context, text, Dimension, Player, Color, Gamemode


class Here(plugins.Plugin):

    @plugins.command
    def here(self, ctx: Context, player_name: Optional[str]=None):
        
        player: Player = None

        if player is not None:
            player = ctx.server.get_player_by_name(player_name)
        else:
            player = ctx.player

        if player is None:
            ctx.reply(text.Text.red(f"Player '{player_name}' is not online!"))

        dim_color = {
            Dimension.Overworld: Color.Green,
            Dimension.Nether: Color.DarkRed,
            Dimension.End: Color.Yellow
        }[player.dimension]

        coords_color = {
            Dimension.Overworld: Color.Blue,
            Dimension.Nether: Color.Red,
            Dimension.End: Color.Gold
        }[player.dimension]

        text_pos = text.Text(player.pos.round(1), color=coords_color)

        if ctx.player.gamemode in [Gamemode.Creative, Gamemode.Spectator]:
            text_pos.hover(text.HoverAction.ShowText, "Click to teleport").click(
                text.ClickAction.RunCommand,
                f"/execute in {player.dimension.value} run tp {player.name} {player.pos.round(1)}"
            )

        ctx.reply(
            text.Text(ctx.player.name), text.Text(" is at ").aqua(), text_pos + text.Text(" in ").aqua(), text.Text(player.dimension.value, color=dim_color)
        )

        ctx.server.execute(f"/effect give {player} minecraft:glowing 15 0 true")