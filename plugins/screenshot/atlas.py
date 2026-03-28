from typing import Dict, Tuple
from PIL import Image

from .texture_manager import TextureManager


class TextureAtlas:

    def __init__(
        self,
        texture_manager: TextureManager,
        size: int = 1024,
        tile_size: int = 16
    ) -> "TextureAtlas":
        
        self.size = size
        self.tile_size = tile_size
        self.image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        self.manager = texture_manager
        
        self.tiles_per_row = size // tile_size
        self.current_index = 0
        self.uv_map: Dict[Tuple[str, str], Tuple[float, float, float, float]] = {}


    def get_uv(
        self,
        block_name: str,
        face: str
    ) -> Tuple[float, float, float, float]:
        
        key = (block_name, face)
        if key in self.uv_map:
            return self.uv_map[key]

        img = self.manager.get_texture(block_name, face)

        if not img:
            img = Image.new("RGBA", (self.tile_size, self.tile_size), (255, 0, 255, 255))
        else:
            img = img.resize((self.tile_size, self.tile_size), Image.NEAREST)

        x = (self.current_index % self.tiles_per_row) * self.tile_size
        y = (self.current_index // self.tiles_per_row) * self.tile_size
        self.image.paste(img, (x, y))
        self.current_index += 1

        u0, v0 = x / self.size, y / self.size
        u1, v1 = (x + self.tile_size) / self.size, (y + self.tile_size) / self.size
        
        self.uv_map[key] = (u0, v0, u1, v1)
        return self.uv_map[key]