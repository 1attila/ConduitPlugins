from typing import Dict, List, Callable, Any
import threading
import asyncio

from mconduit import plugins
from discord.ext import commands
import discord


class Config(plugins.Config):
    bot_token: str
    bot_prefix: str # Defaults to conduit command prefix
    owner_roles: list = []
    admin_roles: list = []
    helper_roles: list = []
    member_roles: list = []
    guest_roles: list = []


class Bot(commands.Bot):
    """
    Conduit bot
    """

    
    __token: str
    __messages_listeners: Dict[int, List[Callable]]


    def __init__(self,
                 token: str,
                 prefix: str
                ) -> "Bot":
    
        super().__init__(command_prefix=prefix, intents=discord.Intents.all())

        self.__token = token
        self.__messages_listeners = {}
    

    async def start_loop(self) -> None:
        await self.start(self.__token)
    

    def _add_listener(self, *channels, fallback: Callable[[discord.Message], Any]) -> None:
        
        for channel in channels:
            self.__messages_listeners.setdefault(channel, []).append(fallback)


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

        await self.process_commands(message)
    

class DiscordExt(plugins.Plugin[Config]):
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


    def _loop(self) -> None:

        asyncio.set_event_loop(self.__loop)

        while True:
            self.__loop.create_task(self.__bot.start_loop())

            try:
                self.__loop.run_forever()
            except Exception as e:
                print(e)

            finally:

                try:
                    self.__loop.run_until_complete(self.__bot.close())
                except Exception as e:
                    print(e)

                self.__loop.close()

    
    def send_message(self, channel_id: int, msg: str) -> None:
        
        fut = asyncio.run_coroutine_threadsafe(self._send_message_coro(channel_id, msg), self.__loop)
        
        return fut.result()


    async def _send_message_coro(self, channel_id: int, msg: str) -> None:

        channel = self.__bot.get_channel(channel_id) or await self.__bot.fetch_channel(channel_id)
        
        if channel is None:
            raise RuntimeError(f"Could not get the channel with id {channel_id}")

        await channel.send(msg)
        

    def subscribe_to(self, *channels: int, fallback: Callable):
        """
        Adds a fallback every time that a new messages arrives in the given channel(s)
        """

        self.__bot._add_listener(*channels, fallback=fallback)