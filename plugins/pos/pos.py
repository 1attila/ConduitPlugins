from typing import Optional

from mconduit import plugins, Context, text, Dimension, Player, Color, Gamemode


class Pos(plugins.Plugin):
    """
    Displays player position
    """


    def add_waypoint(
                     self,
                     name: str,
                     x: int,
                     y: int,
                     z: int,
                     dim: Dimension
        ) -> text.Text:
        """
        Creates a Json Text with the commands to add Xaeros, Voxel and Conduit waypoints 
        """

        x, y, z = int(x), int(y), int(z)

        if not isinstance(dim, str):
            dim = dim.value

        voxel_command = f"/newWaypoint x:{x} y:{y} z:{z} dim:{dim}"
        xaero_command = f"xaero_waypoint_add:{name}:{name[0]}:{x}:{y}:{z}:6:false:0:Internal_{dim}_waypoints"

        voxel_text = text.aqua("[+V]").underlined()
        voxel_text.hover(show_text=text.aqua("Voxel") + text.gray(" waypoint"))
        voxel_text.click(run_command=voxel_command)

        xaero_text = text.gold("[+X]").underlined()
        xaero_text.hover(show_text=text.gold("Xaero") + text.gray(" waypoint"))
        xaero_text.click(suggest_command=xaero_command)

        voxel_text += " "
        voxel_text += xaero_text

        waypoint = self.manager.get_plugin_named("waypoint")
        where = self.manager.get_plugin_named("where") # TODO

        if waypoint is not None:

            waypoint_new = waypoint.get_command_named("waypoint", "new").fallback

            conduit_text = text.dark_aqua("[+C]").underlined()
            conduit_text.hover(show_text=text.dark_aqua("Conduit") + text.gray(" waypoint"))
            conduit_text.click(run_function=lambda ctx: waypoint_new(ctx, name, x, y, z, dim))

            voxel_text += " "
            voxel_text += conduit_text

        return voxel_text


    @plugins.command
    def pos(self, ctx: Context, player_name: Optional[str]=None):
        
        player: Player = None

        if player_name is not None:
            player = ctx.server.get_player_by_name(player_name)
        else:
            player = ctx.player
        
        if player is None:
            ctx.error(f"Player '{player_name}' is not online!")
            return

        player_dim = player.dimension
        player_pos = player.pos.round(1)
        
        dim_color = {
            Dimension.Overworld: Color.DarkGreen,
            Dimension.Nether:    Color.DarkRed,
            Dimension.End:       Color.Gold
        }[player_dim]

        coords_color = {
            Dimension.Overworld: Color.Green,
            Dimension.Nether:    Color.Red,
            Dimension.End:       Color.Yellow
        }[player_dim]
        
        text_pos = text.Text(player_pos, color=coords_color)

        def _try_tp(c: Context):

            if c.player.gamemode != Gamemode.Spectator:
                c.error("You must be in spectator!")
                return
            c.server.execute(f"/execute in {player_dim.value} run tp {player} {player_pos}")
        
        text_pos.hover(show_text="Click to teleport")
        text_pos.click(run_function=_try_tp)
        
        msg = text.dark_gray(player.name)
        msg += text.dark_aqua(" is @ ")
        msg += text_pos + text.dark_aqua(" in ")
        msg += text.Text(player_dim.value, color=dim_color)
        msg += " "
        msg += self.add_waypoint(f"{player_name}s location", *player_pos.as_tuple(), player_dim.value)
        
        if player_name is None:
            
            ctx.say(msg)
        else:
            ctx.reply(msg)

        ctx.server.execute(f"/effect give {player} minecraft:glowing 15 0 true")