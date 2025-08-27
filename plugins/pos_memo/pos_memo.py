from mconduit import plugins, Context, text, Gamemode, Vec3d, Dimension, Color


class Persistent(plugins.Persistent):
    players_pos: dict = {}


class PosMemo(plugins.Plugin[None, Persistent]):
    """
    Memorizes the player position and rotation
    """


    pm = plugins.Command.group(name="posmemo", aliases=["pm"])

    
    @pm.command
    def new(self, ctx: Context, name: str):
        """
        Memorizes the current player pos and rotation
        """

        self.persistent.players_pos[name] = (
            ctx.player.dimension.value,
            *ctx.player.pos.as_tuple(),
            *ctx.player.rotation.as_tuple()
        )
        self.persistent._save()

        ctx.success(f"Position `{name}` saved sucesfully!")

        msg = text.gray(f"Type `!!pm tp {name}` to tp to it!")
        msg.hover(how_text="Click to paste in chat")
        msg.click(suggest_command=f"!!pm tp {name}")
        
        ctx.reply(msg)

    
    @pm.command(name="list", aliases=["l"])
    def _list(self, ctx: Context):
        """
        Lists all the saved pos
        """

        positions = " ".join([pos_name for pos_name in self.persistent.players_pos.keys()])
        ctx.info(f"Saved pos: {positions}")


    @pm.command(aliases=["del", "d"], checks=[plugins.check_perms(plugins.Permission.Helper)])
    def delete(self, ctx: Context, name: str):
        """
        Cancels the saved player data from memory
        """

        if name not in self.persistent.players_pos.keys():

            ctx.error(f"Position `{name}` doesn't exist!")
            return

        self.persistent.players_pos.pop(name)
        self.persistent._save()

        ctx.success(f"Position `{name}` deleted sucesfully!")


    @pm.command
    def get(self, ctx: Context, name: str):
        """
        Retrieves the saved data from memory
        """

        if name not in self.persistent.players_pos.keys():

            ctx.error(f"Position `{name}` doesn't exist!")
            return
        
        dim, x, y, z, _yaw, _pitch = self.persistent.players_pos[name]

        dim_color = {
            Dimension.Overworld: Color.DarkGreen,
            Dimension.Nether:    Color.DarkRed,
            Dimension.End:       Color.Gold
        }[dim]

        coords_color = {
            Dimension.Overworld: Color.Green,
            Dimension.Nether:    Color.Red,
            Dimension.End:       Color.Yellow
        }[dim]

        msg = text.gray(f"Position `{name}` is at ")
        msg += text.Text(f"{x} {y} {z}", coords_color)
        msg += "is at"
        msg += text.Text(f"{dim}", dim_color)
        
        ctx.reply(msg)
        

    @pm.command
    def tp(self, ctx: Context, name: str):
        """
        Teleports the player at the saved data
        """

        if name not in self.persistent.players_pos.keys():

            ctx.error(f"Position `{name}` doesn't exist!")
            return
        
        dim, x, y, z, yaw, pitch = self.persistent.players_pos[name]

        if ctx.player.name not in ctx.server.ops:

            if ctx.player.gamemode not in [Gamemode.Creative, Gamemode.Spectator]:

                if ctx.player.dimension != dim:
                    ctx.error("Player is not in the same dimension!")
                    return

                pos = Vec3d(x, y, z)

                if pos.len() - ctx.player.pos.len() > 1:
                    ctx.error(f"Player is too far from the location ({len(pos - ctx.player.pos)} blocks)")
                    ctx.info("Max distance allowed is less than 1 block")
                    return

        self.server.execute(f"/execute in {dim} run tp {ctx.player.name} {x} {y} {z} {yaw} {pitch}")

        ctx.success(f"Sucesfully teleported to `{name}`!")