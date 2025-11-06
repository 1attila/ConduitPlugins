from typing import Optional
from mconduit import plugins, Context, text, Gamemode, Vec3d

from math import sqrt


class Persistent(plugins.Persistent):
    waypoints: dict = {}


class Waypoint(plugins.Plugin[None, Persistent]):
    """
    Waypoint handler
    """


    @plugins.command(aliases=["wp"])
    def waypoint(self, ctx: Context, name: str):
        """
        Displays a waypoint
        """

        if name not in self.persistent.waypoints.keys():
            
            ctx.error(f"There is no waypoint named `{name}`!")
            return
        
        x, y, z, dim = self.persistent.waypoints[name]

        w = text.Text(f"{name} @ {x} {y}, {z} in {dim}")

        if ctx.player.gamemode in [Gamemode.Creative, Gamemode.Spectator]:

            w.hover(show_text="Click to teleport")
            w.click(run_command=f"/execute if entity @a[name={ctx.player.name}, gamemode=spectator] run execute in {dim} run tp {ctx.player.name} {x} {y} {z}")

        ctx.info(w)


    @waypoint.command(aliases=["create"])
    def add(self,
            ctx: Context,
            name: str,
            x: Optional[float]=None,
            y: Optional[float]=None,
            z: Optional[float]=None,
            overwrite: plugins.Flag=False
        ):
        """
        Creates a new waypoint
        """

        
        if name in self.persistent.waypoints.keys() and not overwrite:
            
            ctx.error(f"There is already a waypoint named `{name}`!")
            return
        
        if name in self.persistent.waypoints.keys() and overwrite:
            ctx.warn(f"Overwriting `{name}`")
        
        use_player_pos = x is None or y is None or z is None
        
        if use_player_pos is True:
            x, y, z = ctx.player.pos.as_tuple()
        
        dim = ctx.player.dimension.value
        
        self.persistent.waypoints[name] = x, y, z, dim
        self.persistent._save()

        msg = text.Text(f"Waypoint `{name}` saved sucesfully")

        if use_player_pos is True:
            msg += text.Text(" from player pos")

        msg += "!"
        ctx.success(msg)


    @waypoint.command(name="list", aliases=["l"])
    def _list(self, ctx: Context):
        """
        Lists all waypoints
        """

        if len(self.persistent.waypoints.keys()) < 1:

            ctx.warn("There are no waypoints!")
            return

        ctx.reply(text.aqua("Waypoints:"))

        for i, waypoint in enumerate(self.persistent.waypoints.keys()):
            
            x, y, z, dim = self.persistent.waypoints[waypoint]

            w = text.Text(f"#{i}: {waypoint} @ {round(x, 2)} {round(y, 2)} {round(z, 2)} in {dim}")

            if ctx.player.gamemode in [Gamemode.Creative, Gamemode.Spectator]:

                w.hover(show_text="Click to teleport")
                w.click(run_command=f"/execute if entity @a[name={ctx.player.name}, gamemode=spectator] run execute in {dim} run tp {ctx.player.name} {x} {y} {z}")

            ctx.info(w)
        

    @waypoint.command(aliases=["del"], checks=[plugins.check_perms(plugins.Permission.Helper)])
    def delete(self, ctx: Context, name: str):
        """
        Deletes the specified waypoint
        """

        if name not in self.persistent.waypoints.keys():
            
            ctx.error(f"There is no waypoint named `{name}`!")
            return
        
        self.persistent.waypoints.pop(name)
        self.persistent._save()

        ctx.success(f"Waypoint `{name}` removed sucesfully!")

    
    @waypoint.command(aliases=["del"], checks=[plugins.check_perms(plugins.Permission.Helper)])
    def rename(self, ctx: Context, name: str, new_name: str):
        """
        Renames the specified waypoint
        """

        if name not in self.persistent.waypoints.keys():
            
            ctx.error(f"There is no waypoint named `{name}`!")
            return
        
        if new_name in self.persistent.waypoints.keys():

            ctx.error(f"Theres a waypoint already named `{new_name}`!")
            return
        
        self.persistent.waypoints[new_name] = self.persistent.waypoints[name]
        self.persistent.waypoints.pop(name)
        self.persistent._save()

        ctx.success(f"Waypoint `{name}` renamed sucesfully to {new_name}!")

    
    @waypoint.command
    def nearest(self, ctx: Context, limit: int=1):
        """
        Displays the nearest waypoint
        """

        if len(self.persistent.waypoints.keys()) < 1:

            ctx.warn("There are no waypoints!")
            return

        dim = ctx.player.dimension.value
        pos = ctx.player.pos

        nearest = {}
        differences = []

        for w_name, w_data in self.persistent.waypoints.items():

            wx, wz, wy, wdim = w_data

            if dim != wdim:
                continue

            diff = (pos - Vec3d(wx, wy, wz)).len

            nearest[diff] = w_name
            differences.append(diff)

        if len(nearest.keys()) < 1:
            ctx.warn("There are no waypoints in your dimension!")

        ctx.reply(text.aqua("Nearest waypoints:"))

        differences = sorted(differences)

        for i in range(limit):

            if i >= len(differences):
                break

            diff = differences[i]

            msg = text.Text(f"#{i}: {nearest[diff]} dist: {sqrt(diff)}")

            if ctx.player.gamemode in [Gamemode.Creative, Gamemode.Spectator]:

                x, y, z, dim = self.persistent.waypoints[nearest[diff]]

                msg.hover(show_text="Click to teleport")
                msg.click(run_command=f"/execute if entity @a[name={ctx.player.name}, gamemode=spectator] run execute in {dim} run tp {ctx.player.name} {x} {y} {z}")
            
            ctx.info(msg)