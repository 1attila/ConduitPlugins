from typing import Optional, TYPE_CHECKING

from discord.ext import commands
import discord

if TYPE_CHECKING:
    from .discord_ext import DiscordExt

    plugin: DiscordExt
else:
    from mconduit.plugins import Plugin

    plugin: Plugin


class BuiltinPluign(commands.Cog):
    """
    Conduit utilities
    """

    bot: commands.Bot


    def __init__(self, bot: commands.Bot) -> "BuiltinPlugin":
        self.bot = bot

    
    @commands.command()
    async def version(self, ctx: commands.Context):
        ...

    
    @commands.command()
    async def news(self, ctx: commands.Context):
        ...

    
    @commands.command()
    async def uptime(self, ctx: commands.Context):
        ...

    
    @commands.command()
    async def plugin(self, ctx: commands.Context):
        ...


async def setup(bot: commands.Bot):
    await bot.add_cog(BuiltinPlugin(bot))