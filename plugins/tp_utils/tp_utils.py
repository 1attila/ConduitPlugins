from typing import Dict, List, Tuple

from mconduit import plugins, text, Context, Gamemode, Vec3d, Dimension
from mconduit.utils.coords import ow_to_nether


class InvalidInput(Exception):
    ...

class LocationNotFound(Exception):
    ...


class Persistent(plugins.Persistent):
    original_pos: Dict[str, List] = {}


class TpUtils(plugins.Plugin[None, Persistent]):
    """
    Tp utilities
    """


    def _parse_dimension(self, dimension: str) -> Dimension:

        try:
            return {
                "overworld": Dimension.Overworld,
                "ow": Dimension.Overworld,
                "the_nether": Dimension.Nether,
                "nether": Dimension.Nether,
                "the_end": Dimension.End,
                "end": Dimension.End
            }[dimension.strip().lower()]

        except:
            raise InvalidInput


    def _location_to_coords(self, ctx: Context, *args) -> Tuple[Vec3d, Dimension]:
        """
        Return the location coords and dimension whatever it's type is (raw coords, player or waypoint)
        """

        if len(args) == 3:

            x, y, z = args

            try:
                x = int(x)
                y = int(y)
                z = int(z)

                return Vec3d(x, y, z), ctx.player.dimension

            except:
                raise InvalidInput

        elif len(args) == 4:

            x, y, z, dimension = args 

            try:
                x = int(x)
                y = int(y)
                z = int(z)

                dimension = self._parse_dimension(dimension)

                return Vec3d(x, y, z), dimension

            except:
                raise InvalidInput
        
        if len(args) != 1:
            raise InvalidInput
        
        waypoint = self.manager.get_plugin_named("waypoint")

        if waypoint is not None:

            if args in waypoint.persistent.waypoints:
                
                x, y, z, dim = waypoint.persistent.waypoints[args]

                try:
                    dimension = self._parse_dimension(dim)
                except:
                    raise InvalidInput

                return Vec3d(x, y, z), dimension

        for player in self.server.get_online_players():

            if args in player.name:
                return player.pos, player.dimension
            
        raise LocationNotFound
    

    def teleport(self,
                 ctx: Context,
                 pos: Vec3d,
                 dim: Dimension
                ):
        """
        - Teleports the given player to the given pos and dimension
        - Saves its position before teleporting to support rollback
        - Displays success on actionbar
        """

        orig_pos = ctx.player.pos
        self.persistent.original_pos[ctx.player.name] = *orig_pos.as_tuple(), ctx.player.dimension.value
        self.persistent._save()

        self.server.execute(f"/execute in {dim} run tp {ctx.player} {pos}")

        msg = text.dark_aqua(f"Teleported: [")
        msg += text.gold(orig_pos.round(1))
        msg += text.dark_aqua("] --> [")
        msg += text.green(pos.round(1))
        msg += text.dark_aqua("]")

        self.server.execute(f"/title {ctx.player} actionbar {msg}")


    @plugins.command
    def tp(self, ctx: Context, location_args: list[str]):
        """
        Tp the player who sent this command to the given location
        """

        if ctx.player.gamemode not in [Gamemode.Spectator, Gamemode.Creative]:
            ctx.error("You must be in spectator or creative!")
            return
        
        pos, dim = self._location_to_coords(ctx, *location_args)

        self.teleport(ctx, pos, dim)

    
    @plugins.command
    def forward(self, ctx: Context, distance: float=250):
        """
        Tps the player who sent this command forward by the given distance
        """
        
        if ctx.player.gamemode not in [Gamemode.Spectator, Gamemode.Creative]:
            ctx.error("You must be in spectator or creative!")
            return

        new_pos = ctx.player.pos + ctx.player.forward_vec * distance

        self.teleport(ctx, new_pos, ctx.player.dimension)


    @plugins.command
    def back(self, ctx: Context):
        """
        Teleports you back to the position before the teleport
        """
        
        if ctx.player.name not in self.persistent.original_pos:
            
            err = text.red("Theres no position saved!")
            self.server.execute(f"title {ctx.player} actionbar {err}")
            return

        if ctx.player.gamemode not in [Gamemode.Spectator, Gamemode.Creative]:

            err = text.red("You must be in spectator or creative!")
            self.server.execute(f"title {ctx.player} actionbar {err}")
            return

        x, y, z, dim = self.persistent.original_pos[ctx.player.name]

        self.teleport(ctx, Vec3d(x, y, z), dim)

    
    @plugins.command
    def end(self, ctx: Context):
        """
        Teleports yourself in the end
        """

        if ctx.player.dimension == Dimension.End:

            err = text.red("You are already in the end!")
            self.server.execute(f"title {ctx.player} actionbar {err}")
            return
        
        if ctx.player.gamemode not in [Gamemode.Spectator, Gamemode.Creative]:

            err = text.red("You must be in spectator or creative!")
            self.server.execute(f"title {ctx.player} actionbar {err}")
            return

        coords = ctx.player.pos

        if ctx.player.dimension == Dimension.Nether:
            coords = coords * 8

        self.teleport(ctx, coords, Dimension.End)



    @plugins.command(aliases=["net"])
    def nether(self, ctx: Context):
        """
        Teleports yourself in the nether (with rescaled coords)
        """

        if ctx.player.dimension == Dimension.Nether:

            err = text.red("You are already in the nether!")
            self.server.execute(f"title {ctx.player} actionbar {err}")
            return
        
        if ctx.player.gamemode not in [Gamemode.Spectator, Gamemode.Creative]:

            err = text.red("You must be in spectator or creative!")
            self.server.execute(f"title {ctx.player} actionbar {err}")
            return

        self.teleport(ctx, ow_to_nether(ctx.player.pos), Dimension.Nether)

    
    @plugins.command(aliases=["ow", "ov"])
    def overworld(self, ctx: Context):
        """
        Teleports yourself in the overworld
        """

        if ctx.player.dimension == Dimension.Overworld:

            err = text.red("You are already in the overworld!")
            self.server.execute(f"title {ctx.player} actionbar {err}")
            return
        
        if ctx.player.gamemode not in [Gamemode.Spectator, Gamemode.Creative]:

            err = text.red("You must be in spectator or creative!")
            self.server.execute(f"title {ctx.player} actionbar {err}")
            return

        coords = ctx.player.pos

        if ctx.player.dimension == Dimension.Nether:
            coords = coords * 8

        self.teleport(ctx, coords, Dimension.Overworld)