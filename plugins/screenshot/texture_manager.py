from typing import Optional, Dict
from pathlib import Path
from PIL import Image


class TextureManager:
    
    __base_path: Path
    __current_texture: Path
    __cache: Dict[str, Image]
    

    def __init__(
        self,
        base_path: Path,
        texture_pack: str = "vanilla"
    ) -> "TextureManager":
        
        self.__base_path = base_path
        self.__current_texture = Path.cwd()
        self.__cache = {}
        self.load_texture_pack(texture_pack)

    
    def load_texture_pack(self, texture_pack: str) -> None:

        texture_path = self.__base_path / "textures" / texture_pack

        if not texture_path.exists():
            ValueError(f"Cound not found texture named {texture_pack} inside /textures")

        self.__current_texture = texture_path
        self.__cache = {}


    def get_texture_path(
        self,
        block_name: str,
        face: str | None = None
    ) -> Optional[Path]:

        if block_name == "magma_block":
            block_name = "magma"

        if block_name == "trial_spawner" and face != "bottom":
            block_name =  "trial_spawner_side_active"

        block_name = block_name.replace("waxed", "")
        
        attempts = ["", "side", "0"] # '0' is for suspicious_gravel

        if face is not None:
            attempts.insert(0, face)

        for attempt in attempts:
            
            if attempt != "":
                attempt = "_" + attempt

            texture_path = (self.__current_texture / (block_name + attempt)).with_suffix(".png")
            
            if texture_path.exists():
                return texture_path

        
    def get_texture(
        self,
        block_name: str,
        face: str | None = None,
    ) -> Optional[Image]:

        block = block_name.replace("minecraft:", "")

        if (block, face) in self.__cache:
            return self.__cache[(block, face)]
        
        texture_path = self.get_texture_path(block, face)
    
        if texture_path is None:
            print("No texture", block, face)
            return

        img = Image.open(texture_path).convert("RGBA")
        self.__cache[(block, face)] = img

        return img