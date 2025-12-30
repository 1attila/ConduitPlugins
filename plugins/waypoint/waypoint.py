from typing import Optional
from mconduit import plugins, Context, text, Gamemode, Vec3d, Dimension

from math import sqrt


class Persistent(plugins.Persistent):
    waypoints: dict = {}


def add_waypoint(
                 name: str,
                 x: int,
                 y: int,
                 z: int,
                 dim: Dimension
    ) -> text.Text:
    """
    Creates a Json Text with the commands to add Xaeros and Voxel waypoints 
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
    xaero_text.click(run_command=xaero_command)

    return voxel_text + " " + xaero_text


class Waypoint(plugins.Plugin[None, Persistent]):
    """
    Waypoint handler
    """


    def _waypoint_text(self, waypoint: str) -> text.Text:
        """
        Return a Json Text to represent the given waypoint
        """

        x, y, z, dim = self.persistent.waypoints[waypoint]

        w = text.Text(f"{waypoint} @ {round(x, 2)} {round(y, 2)}, {round(z, 2)} in {dim}")
        w += " "
        w += add_waypoint(waypoint, x, y, z, dim)

        def _try_tp(c: Context):

            if c.player.gamemode != Gamemode.Spectator:
                c.error("You must be in spectator!")
                return
            c.server.execute(f"/execute in {dim} run tp {c.player} {x} {y} {z}")

        w.hover(show_text="Click to teleport")
        w.click(run_function=_try_tp)

        return w


    @plugins.command(aliases=["wp"])
    def waypoint(self, ctx: Context, name: str):
        """
        Displays a waypoint
        """

        if name not in self.persistent.waypoints.keys():
            
            ctx.error(f"There is no waypoint named `{name}`!")
            return

        ctx.info(self._waypoint_text(name))


    @waypoint.command
    def new(self,
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

        msg = text.green(f"Waypoint `{name}` saved sucesfully")

        if use_player_pos is True:
            msg += text.green(" from player pos")

        msg += " "
        msg += add_waypoint(name, x, y, z, dim)
        
        ctx.reply(msg)


    @waypoint.command(name="list", aliases=["l"])
    def _list(self, ctx: Context):
        """
        Lists all waypoints
        """
        
        if len(self.persistent.waypoints.keys()) < 1:

            ctx.warn("There are no waypoints!")
            return

        ctx.reply(text.dark_aqua("Waypoints:"))

        for i, waypoint in enumerate(self.persistent.waypoints.keys()):

            w = text.Text(f"#{i}: ") + self._waypoint_text(waypoint)
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
            return

        ctx.reply(text.dark_aqua("Nearest waypoints:"))

        differences = sorted(differences)

        for i in range(limit):

            if i >= len(differences):
                break

            diff = differences[i]
            x, y, z, dim = self.persistent.waypoints[nearest[diff]]

            msg = text.Text(f"#{i}: ") + self._waypoint_text(nearest[diff]) + text.gray(f"dist: {sqrt(diff)}")
            msg += " "
            msg += add_waypoint(nearest[diff], x, y, z, dim)

            ctx.info(msg)