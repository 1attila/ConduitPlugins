from typing import Optional, Literal, List

from mconduit import plugins, utils, Context, Vec3d, Dimension
from mconduit.world import CachedWorldReader


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


    def scan(
        self,
        c1: Vec3d,
        c2: Vec3d,
        dim: Dimension,
        blocks: List[str],
        scan_mode: Literal["replace", "list"] = "list"
    ) -> List[Vec3d] | None:
        
        match scan_mode:

            case "list":
                return self.scan_list(c1, c2, dim, blocks)
        
            case "replace":

                with self.server.all_at_once():
                    
                    for block in BLOCK_LIST:
                        self.server.execute(f"/execute in {dim} fill {c1} {c2} air replace {block}")
            case _:
                raise ValueError("Invalid scan mode")

    
    def scan_list(
        self,
        c1: Vec3d,
        c2: Vec3d,
        dim: Dimension,
        blocks: List[str]
    ) -> List[Vec3d]:

        x1, _y1, z1 = utils.coords.chunk_coords(c1)
        x2, _y2, z2 = utils.coords.chunk_coords(c2)
        max_y, min_y = max(c1.y, c2.y), min(c1.y, c2.y)

        chunks = CachedWorldReader(self.server).get_chunks(x1, z1, x2, z2, dim)
        block_coords = []

        for chunk in chunks:

            for x in range(16):
                for z in range(16):

                    cx, cz = chunk.x, chunk.z

                    for y in range(min_y, max_y):
                    
                        block = chunk.get_block(x, y, z) # Note: This should accept both real and relative coordinates!

                        if block is None:
                            continue
                    
                        block = block.replace("minecraft:", "")
                    
                        if block in blocks:
                            block_coords.append(Vec3d(x + cx * 16, y, z + cz * 16))

        return block_coords
    
    
    @plugins.command(checks=[plugins.check_perms(plugins.Permission.Helper)])
    def scanner(
        self,
        ctx: Context,
        x1: int,
        y1: int,
        z1: int,
        x2: Optional[int] = None,
        y2: Optional[int] = None,
        z2: Optional[int] = None,
        remove: plugins.Flag = False
    ):
        """
        Scans the terrain and removes immovable blocks
        """

        if None in (x2, y2, z2):

            c2 = ctx.player.pos
            c1 = c2 + Vec3d(x2, y2, z2)

        result = self.scan(
            c1, c2,
            ctx.player.dimension,
            BLOCK_LIST,
            "replace" if remove is True else "list"
        )

        if remove is True:
            ctx.success("Removed all the un-movable blocks!")
        else:
            result = ", ".join(result)
            ctx.info(f"Unmovable Blocks: ({len(result)}): {result}")