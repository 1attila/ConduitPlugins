from typing import Optional
import time

from mconduit import plugins, Context, Vec3d, text


BLOCK_LIST = [
    "obsidian",
    "crying_obsidian",
    "spawner",
    "chest",
    "trapped_chest",
    "bedrock",
    "sculk_sensor",
    "dropper",
    "dispenser",
    "furnace",
    "barrier",
    "beacon",
    "command_block",
    "enchanting_table",
    "end_gateway",
    "end_portal",
    "end_portal_frame",
    "ender_chest",
    "grindstone",
    "jigsaw",
    "jukebox",
    "lodestone",
    "nether_portal",
    "barrel",
    "respawn_anchor",
    "beehive",
    "bee_nest",
    "blas_furnace",
    "brewing_stand",
    "dayligth_detector",
    "hopper",
    "smoker"
]


class TerrainScanner(plugins.Plugin):
    """
    Helps prepping the terrain for a World Eater
    """

    
    @plugins.command(checks=[plugins.check_perms(plugins.Permission.Helper)])
    def scanner(self, ctx: Context, x1: int, y1: int, z1: int, x2: Optional[int]=None, y2: Optional[int]=None, z2: Optional[int]=None, pos: plugins.Flag=False, not_remove: plugins.Flag=False):
        """
        Scans the terrain and removes immovable blocks
        """

        if pos is True:

            x1, y1, z1 = ctx.player.pos.as_tuple()
            x2, y2, z2 = (ctx.player.pos + Vec3d(x2, y2, z2)).as_tuple()

        dim = ctx.player.dimension

        if not_remove is False:
            
            t0 = time.time()

            with ctx.server.all_at_once():

                for block in BLOCK_LIST:
                    ctx.server.execute(f"/execute in {dim} fill {x1} {y1} {z1} {x2} {y2} {z2} air replace {block}")

            ctx.reply(text.green("All the locks have been removed"), text.gray(f", took {time.time() - t0}s"))
            
            return

        raise NotImplementedError()