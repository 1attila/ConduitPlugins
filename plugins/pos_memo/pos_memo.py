from mconduit import plugins, Context, text, Gamemode, Vec3d, Dimension, Color


class PosMemo(plugins.Plugin):
    """
    Memorizes the player position and rotation
    """


    pm = plugins.Command.group(name="posmemo", aliases=["pm"])


    def __init__(self, manager, metadata, lang) -> "PosMemo":

        super().__init__(manager, metadata, lang)

        try:
            self.persistent.players_pos
        except Exception as e:
            self.persistent.players_pos = {}

    
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
        ctx.reply(text.gray(f"Type `!!pm tp {name}` to tp to it!").hover(
            show_text="Click to paste in chat").click(
            suggest_command=f"!!pm tp {name}")
        )

    
    @pm.command
    def list(self, ctx: Context):
        """
        Lists all the saved pos
        """

        positions = " ".join([pos_name for pos_name in self.persistent.players_pos.keys()])
        ctx.info(f"Saved pos: {positions}")


    @pm.command
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
            Dimension.Overworld: Color.Green,
            Dimension.Nether:    Color.DarkRed,
            Dimension.End:       Color.Yellow
        }[dim]

        coords_color = {
            Dimension.Overworld: Color.Blue,
            Dimension.Nether:    Color.Red,
            Dimension.End:       Color.Gold
        }[dim]

        ctx.reply(text.gray(f"Position `{name}` is at ") + text.Text(
            f"{x} {y} {z}", coords_color) + "is at" + text.Text(
            f"{dim}", dim_color)
        )
        

    @pm.command
    def tp(self, ctx: Context, name: str):
        """
        Teleports the player at the saved data
        """

        if name not in self.persistent.players_pos.keys():

            ctx.error(f"Position `{name}` doesn't exist!")
            return
        
        dim, x, y, z, yaw, pitch = self.persistent.players_pos[name]

        if ctx.player.name not in ctx.server.op:

            if ctx.player.gamemode not in  [Gamemode.Creative, Gamemode.Spectator]:

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