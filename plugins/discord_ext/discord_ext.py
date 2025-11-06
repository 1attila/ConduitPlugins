from typing import Optional, Dict, List, Callable, Any
import threading
import asyncio

from mconduit import plugins, Player
from discord.ext import commands
from cleantext import clean
import discord


class Config(plugins.Config):
    bot_token: str
    
    bot_prefix: str # Defaults to conduit command prefix
    owner_roles: list = []
    admin_roles: list = []
    helper_roles: list = []
    member_roles: list = []
    guest_roles: list = []

    embeds_config: dict = {
        "color": None, # HEX, 3498DB
        "footer-text": "",
        "footer-image-url": ""
    }

    enable_players_bind: bool = True
    players_bind: list = []


class Bot(commands.Bot):
    """
    Conduit bot
    """

    
    __token: str
    __messages_listeners: Dict[int, List[Callable[[discord.Message], Any]]]
    ready_event: asyncio.Event


    def __init__(self,
                 token: str,
                 prefix: str
                ) -> "Bot":
    
        super().__init__(command_prefix=prefix, intents=discord.Intents.all())

        self.__token = token
        self.__messages_listeners = {}
        self.ready_event = asyncio.Event()

    async def start_loop(self) -> None:
        await self.start(self.__token, reconnect=True)
    

    def _add_listener(self, *channels, fallback: Callable[[discord.Message], Any]) -> None:
        
        for channel in channels:
            self.__messages_listeners.setdefault(channel, []).append(fallback)


    async def on_ready(self) -> None:

        if not self.ready_event.is_set():
            self.ready_event.set()


    async def on_message(self, message: discord.Message) -> None:
        
        if message.author == self.user:
            return

        for fn in self.__messages_listeners.get(message.channel.id, []):
            try:
                maybe_coro = fn(message)

                if asyncio.is_coroutine(maybe_coro):
                    await maybe_coro
                
            except:
                ...
        try:
            await self.process_commands(message)
        except Exception as e:
            print(e)


class DiscordExt(plugins.Plugin[Config, None]):
    """
    Utility plugin to broadcast between Minecraft and discord
    """


    __bot: Bot
    __loop: asyncio.AbstractEventLoop
    __thread: threading.Thread


    def __init__(self, manager, metadata, lang) -> "DiscordExt":

        super().__init__(manager, metadata, lang)

        if self.config.bot_prefix == "":
            self.config.bot_prefix = self.manager.command_prefix

        self.__bot = Bot(self.config.bot_token, self.config.bot_prefix)

        self.__loop = asyncio.new_event_loop()
        self.__thread = threading.Thread(target=self._loop)
        self.__thread.start()


    def about_to_stop(self):

        asyncio.run_coroutine_threadsafe(self.__bot.close(), self.__loop)
        self.__loop.call_soon_threadsafe(self.__loop.stop())
        self.__thread.join(timeout=5)


    def _loop(self) -> None:

        asyncio.set_event_loop(self.__loop)

        try:
            self.__loop.run_until_complete(self.__bot.start_loop())
        except Exception as e:
            print(e)

        finally:
            try:
                self.__loop.run_until_complete(self.__bot.close())
            except Exception as e:
                print(e)
            
            
            pending = asyncio.all_tasks(loop=self.__loop)

            for task in pending:
                task.cancel()

            try:
                self.__loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            except Exception:
                pass

            self.__loop.close()


    def _format(self, message: str) -> str:
        """
        Formats the role, users and channel tags
        """

        return message

    
    def send_message(self, channel_id: int, msg: str, format: bool=True) -> discord.Message:
        
        if format is True:
            msg = self._format(msg)

        fut = asyncio.run_coroutine_threadsafe(
            self._send_message_coro(channel_id, msg),
            self.__loop
        )
        
        return fut.result()


    async def _send_message_coro(self, channel_id: int, msg: str) -> discord.Message:

        channel = self.__bot.get_channel(channel_id) or await self.__bot.fetch_channel(channel_id)
        
        if channel is None:
            raise RuntimeError(f"Could not get the channel with id {channel_id}")

        try:
            return await channel.send(msg)
        except Exception as e:
            print(e)

    
    def _style_embed(self, embed: discord.Embed) -> discord.Embed:

        if self.config.embeds_config["color"] is not None:
                
            color = self.config.embeds_config["color"]
            color = discord.Colour(int(color, 16))
            embed.color = color

        footer_text = self.config.embeds_config["footer-text"]
        footer_image_url = self.config.embeds_config["footer-image-url"]

        if (
            len(footer_text) > 0 or
            len(footer_image_url) > 0
        ):
            kw = {}

            if len(footer_text) > 0:
                kw["text"] = footer_text

            if len(footer_image_url) > 0:
                kw["icon_url"] = footer_image_url
                
            embed.set_footer(**kw)

        return embed


    def _check_embeds(self, **kwargs) -> dict:

        if "embed" in kwargs:

            embed: discord.Embed = kwargs["embed"]
            kwargs["embed"] = self._style_embed(embed)

        if "embeds" in kwargs:

            embeds = []

            for embed in kwargs["embeds"]:
                embeds.append(self._style_embed(embed))

            kwargs["embeds"] = embeds

        return kwargs

    
    def edit_message(self, channel_id: int, message_id: int, **kwargs) -> discord.Message:
        
        kwargs = self._check_embeds(**kwargs)

        fut = asyncio.run_coroutine_threadsafe(
            self._edit_message_coro(channel_id, message_id, **kwargs),
            self.__loop
        )

        return fut.result()


    async def _edit_message_coro(self, channel_id: int, message_id: int, **kwargs) -> discord.Message:

        try:
            channel = self.__bot.get_channel(channel_id) or await self.__bot.fetch_channel(channel_id)

            if channel is None:
                raise RuntimeError(f"Could not get the channel with id {channel_id}")

            message = await channel.fetch_message(message_id)

            return await message.edit(**kwargs)

        except Exception as e:
            raise e
        

    def subscribe_to(self, *channels: int, fallback: Callable):
        """
        Adds a fallback every time that a new messages arrives in the given channel(s)
        """
        
        self.__bot._add_listener(*channels, fallback=fallback)

    
    def get_player(self, dc_name: str) -> Optional["Player"]:
        """
        Returns the Minecraft player associated with the given discord name
        """
        ...

    def get_user(self, mc_ign: str) -> Optional[discord.User]:
        """
        Returns the discord user associated with the given Minecraft player
        """
        ...