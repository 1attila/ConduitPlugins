from typing import TYPE_CHECKING
from pathlib import Path
from PIL import Image

from discord.ext import commands
import discord

from mconduit import Vec3d, Rot

if TYPE_CHECKING:
    from .screenshot import Screenshot

    plugin: Screenshot
else:
    from mconduit.plugins import Plugin

    plugin: Plugin


def save_image(
    image: Image
) -> Path:
    
    n = 0

    while (plugin.discord_images_path / f"img_{n}.png").exists():
        n += 1

    image_path = plugin.discord_images_path / f"img_{n}.png"
    image.save(image_path)

    return image_path


class ScreenshotCog(commands.Cog):
    """
    !!screenshot command
    """


    bot: commands.Bot
    

    def __init__(self, bot: commands.Bot) -> "ScreenshotCog":
        self.bot = bot

    
    @commands.command()
    async def screenshot(
        self,
        ctx: commands.Context,
        x: int = None, y: int = None, z: int = None,
        yaw: float = None, pitch: float = None,
        dim: str = None,
        fov: int = None,
        max_dist: int = None,
        texture: str = None,
        width: int = None,
        height: int = None
    ):

        if None in (x, y, z):
            pos = None
        else:
            pos = Vec3d(x, y, z)

        if None in (yaw, pitch):
            rot = None
        else:
            rot = Rot(yaw, pitch, degrees=True)
        
        image = plugin.generate_with_default_configs(
            pos,
            rot,
            dim,
            fov,
            max_dist,
            texture,
            width,
            height
        )
        image_path = save_image(image)

        await ctx.channel.send(file=discord.File(image_path))
        await ctx.message.delete()
    

async def setup(bot: commands.Bot):
    await bot.add_cog(ScreenshotCog(bot))