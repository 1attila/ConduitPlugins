from typing import Optional, TYPE_CHECKING

from discord.ext import commands
import discord

if TYPE_CHECKING:
    from .discord_ext import DiscordExt

    plugin: DiscordExt
else:
    from mconduit.plugins import Plugin

    plugin: Plugin


class Online(commands.Cog):
    """
    !!online command
    """


    bot: commands.Bot
    

    def __init__(self, bot: commands.Bot) -> "Online":
        self.bot = bot

    
    @commands.command()
    async def online(self, ctx: commands.Context):
        
        embed = discord.Embed(title="ONLINE PLAYERS")

        for server in plugin.server.handler.servers:
            
            players = server.get_online_players()
            
            if players == None:
                embed.add_field(name=f"{server.name}:", value="Offline")

            elif players == []:
                players = "none"
                embed.add_field(name=f"{server.name}:", value=players)

            else:
                players = [player.name for player in players]
                n_players = len(players)
                players = ", ".join(players)
                embed.add_field(name=f"{server.name} ({n_players}):", value=players)

        embed = plugin._style_embed(embed)

        await ctx.channel.send(embed=embed)
        await ctx.message.delete()
    

async def setup(bot: commands.Bot):
    await bot.add_cog(Online(bot))