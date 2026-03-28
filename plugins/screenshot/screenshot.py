from typing import Optional, Union, Dict, Any
from pathlib import Path
from PIL import Image
import threading

from mconduit import plugins, Context, Vec3d, Rot, Dimension

from .renderer import Renderer


class Persistent(plugins.Persistent):

    pos: list = [0, 0, 0]
    rot: list = [0, 0]
    dim: str = "overworld"
    fov: int = 70
    max_dist: int = 128
    texture: str = "vanilla"
    width: int = 1900
    height: int = 1080


class Screenshot(plugins.Plugin[None, Persistent]):
    """
    Renders a picture as it was taken directly in-game
    """


    __lock: threading.Lock
    screen = plugins.Command.group(
        name = "screen"
    )
    
    
    def on_load(self):

        self.__lock = threading.Lock()

        self.saved_images_path.mkdir(parents=True, exist_ok=True)

        discord_ext = self.manager.get_plugin_named("discord_ext")

        if discord_ext is not None:

            self.discord_images_path.mkdir(parents=True, exist_ok=True)
            discord_ext.load_cog("discord_cog", self)

        self.__renderer = Renderer(self.server, self.path)

    
    @property
    def discord_images_path(self) -> Path:
        """
        Path were discord should save the images
        """

        return self.path / "discord_images" / self.server.name

    
    @property
    def saved_images_path(self) -> Path:
        """
        Path were the images taken are saved
        """

        return self.path / "images" / self.server.name

    
    @property
    def default_configs(self) -> Dict[str, Any]:
        """
        Returns the default configs to generate an image
        """

        return {
            "camera_pos": Vec3d(*self.persistent.pos),
            "camera_rot": Rot(*self.persistent.rot, degrees=True),
            "dimension": self.persistent.dim,
            "fov": self.persistent.fov,
            "max_dist": self.persistent.max_dist,
            "texture": self.persistent.texture,
            "width": self.persistent.width,
            "height": self.persistent.height
        }
    

    def generate_with_default_configs(
        self,
        camera_pos: Optional[Vec3d] = None,
        camera_rot: Optional[Rot] = None,
        dimension: Optional[Dimension] = None,
        fov: Optional[float] = None,
        max_dist: Optional[int] = None,
        texture: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None
    ) -> Image:

        defaults = self.default_configs
        configs = [
            camera_pos,
            camera_rot,
            dimension,
            fov,
            max_dist,
            texture,
            width,
            height
        ]

        for (i, config), default in zip(enumerate(configs), defaults.values()):
            
            if config is None:
                configs[i] = default

        with self.__lock:
            return self.__renderer.generate_picture(*configs)


    def generate_picture(
        self,
        camera_pos: Vec3d,
        camera_rot: Rot = Rot(45, 0, degrees=True),
        dimension: Dimension = Dimension.Overworld,
        fov: float = 70,
        max_dist: int = 128,
        texture: str = "vanilla",
        width: int = 320,
        height: int = 240
    ) -> Image:
        
        with self.__lock:
            return self.__renderer.generate_picture(
                camera_pos,
                camera_rot,
                dimension,
                fov,
                max_dist,
                texture,
                width,
                height
            )
    

    @screen.command
    def take(
        self,
        ctx: Context,
        name: str,
        x: Union[int, str] = "-", y: Union[int, str] = "-", z: Union[int, str] = "-",
        yaw: Union[float, str] = "-", pitch: Union[float, str] = "-",
        dimension: str = "-",
        fov: Union[float, str] = "-",
        max_dist: Union[int, str] = "-",
        texture: str = "-",
        width: Union[int, str] = "-",
        height: Union[int, str] = "-"
    ):
        
        if "-" in (x, y, z):
            pos = ctx.player.pos
        else:
            pos = Vec3d(x, y, z)

        if "-" in (yaw, pitch):
            rot = ctx.player.rotation
        else:
            rot = Rot(yaw, pitch, degrees=True)

        if dimension == "-" :
            dimension = ctx.player.dimension

        configs = [
            fov,
            max_dist,
            texture,
            width,
            height,
        ]

        for i, config in enumerate(configs):

            if config == "-":
                configs[i] = None
        
        img_path = self.saved_images_path / f"{name}.png"

        if img_path.exists():
            ctx.error(f"An image named {name} already exists!")
            return
        
        image = self.generate_with_default_configs(
            pos,
            rot,
            dimension,
            *configs
        )
        
        image.save(img_path)
        
        ctx.success("Image saved sucesfully!")