from pathlib import Path
from PIL import Image

from mconduit import Vec3d, Rot, Dimension, Server
from mconduit.world import WorldReader, Region, Chunk, Block

from .ray import raycast
from .camera import Camera
from .lighting import apply_lighting
from .fog import apply_fog, get_fog_color
from .texture_manager import TextureManager


class CachedWorldReader(WorldReader):


    def __init__(
        self,
        server: Server
    ) -> "CachedWorldReader":

        super().__init__(server)

        self.__region_cache = {}
        self.__chunk_cache = {}
        self.__block_cache = {}


    def clean_cache(self) -> None:

        self.__region_cache = {}
        self.__chunk_cache = {}
        self.__block_cache = {}


    def get_region(
        self,
        region_x: int,
        region_z: int
    ) -> Region | None:

        if (region_x, region_z) in self.__region_cache:
            return self.__region_cache[(region_x, region_z)]

        region = super().get_region(region_x, region_z)
        self.__region_cache[(region_x, region_z)] = region

        return region

    
    def get_chunk(
        self,
        chunk_x: int,
        chunk_z: int
    ) -> Chunk | None:

        if (chunk_x, chunk_z) in self.__chunk_cache:
            return self.__chunk_cache[(chunk_x, chunk_z)]

        chunk = super().get_chunk(chunk_x, chunk_z)
        self.__chunk_cache[(chunk_x, chunk_z)] = chunk

        return chunk

    
    def get_block(self, block_pos: Vec3d) -> Block | None:

        if block_pos in self.__block_cache:
            return self.__block_cache[block_pos]

        block = super().get_block(block_pos)
        self.__block_cache[block_pos] = block

        return block


class Renderer:


    def __init__(
        self,
        server: Server,
        base_path: Path
    ) -> "Renderer":
        
        self.server = server
        self.world_reader = CachedWorldReader(server)
        self.texture_manager = TextureManager(base_path)


    def generate_picture(
        self,
        pos: Vec3d,
        rot: Rot,
        dim: Dimension,
        fov: float,
        texture: str,
        width: int,
        height: int
    ) -> Image:
        
        img = Image.new("RGBA", (width, height))
        pixels = img.load()

        self.world_reader.clean_cache()
        self.texture_manager.load_texture_pack(texture)
        camera = Camera(*pos.as_tuple(), rot.yaw, rot.pitch, fov)
        fog_color = get_fog_color(dim)

        for py in range(height):

            for px in range(width):

                direction = camera.get_ray_direction(px, py, width, height)
                
                ray = raycast(self.world_reader, pos, direction)

                if ray is None:
                    pixels[px, py] = fog_color
                    continue

                p, block, face, dist = ray
                texture = self.texture_manager.get_texture(block["Name"], face)
                
                if texture is None:
                    print("Texture None", px, py)
                    pixels[px, py] = fog_color
                    continue

                u = int((p.x % 1) * texture.width)
                v = int((p.z % 1) * texture.height)

                color = texture.getpixel((u % texture.width, v % texture.height))
                
                color = apply_lighting(color, face)
                color = apply_fog(color, dist, 200, fog_color)

                pixels[px, py] = color

        return img