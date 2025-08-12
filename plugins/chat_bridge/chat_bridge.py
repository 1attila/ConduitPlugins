from typing import List, Optional, TYPE_CHECKING

from mconduit import plugins, text, Context, Event, At, Message

if TYPE_CHECKING:
    import discord


class ServerDoesntExist(Exception):
    ...

class AlreadyConnected(Exception):
    ...

class ServerDoesntHaveChatBridge(Exception):
    ...

class MissingConnection(Exception):
    ...


class Config(plugins.Config):
    bridge_channel: int=0
    message_filter: list = []


class ChatBridge(plugins.Plugin[Config]):
    """
    Broadcasts between Minecraft servers and discord
    """


    __discord_ext: Optional[plugins.Plugin]
    __discord_enabled: bool
    cb = plugins.Command.group(
        name="chat-bridge", aliases=["cb"]
    )


    def __init__(self, manager, metadata, lang) -> "ChatBridge":
        
        super().__init__(manager, metadata, lang)

        try:
            self.persistent.connections
        except Exception as e:
            self.persistent.connections = [server.name for server in self.servers]
        
        try:
            self.persistent.bridge_channel
        except Exception as e:
            self.persistent.bridge_channel = self.config.bridge_channel
        
        self.__discord_ext = self.manager.get_plugin_named("discord_ext")
        self.__discord_enabled = self.__discord_ext is not None and self.config.bridge_channel != 0
        
        if self.__discord_enabled:
            self.__discord_ext.subscribe_to(self.config.bridge_channel, fallback=self._on_discord_message)
        

    def _get_plugin_instances(self) -> List["ChatBridge"]:
        """
        Returns a list with all the running chat_bridge plugin instances
        """

        plugins = []

        for server in self.persistent.connections:

            server = self.server.handler.get_server_named(server)
            plugins.append(server.plugin_manager.get_plugin_named("chat_bridge"))

        return plugins
    

    @cb.command(name="disconnect")
    def _disconnect(self, ctx: Context, server: str):
        """
        This server won't communicate with the given server anymore
        """

        try:
            server = self.server.handler.get_server_named(server)

            if server is None:
                raise ServerDoesntExist()
            
            plg = self.server.plugin_manager.get_plugin_named("chat_bridge")
            
            if plg is None:
                raise MissingConnection()
            
            plg.disconnect(self.server.name)
            self.connect(server.name)

        except Exception as e:
            raise e


    @cb.command(name="connect")
    def _connect(self, ctx: Context, server: str):
        """
        Starts to communicate with the given server
        """
        
        try:
            server = self.server.handler.get_server_named(server)

            if server is None:
                raise ServerDoesntExist()
            
            plg = self.server.plugin_manager.get_plugin_named("chat_bridge")
            
            if plg is None:
                raise ServerDoesntHaveChatBridge()
            
            plg.connect(self.server.name)
            self.connect(server.name)
        
        except Exception as e:
            raise e
        

    def connect(self, server: str):
        
        if server in self.persistent.connections:
            raise AlreadyConnected()

        if server not in self.servers:
            raise ServerDoesntHaveChatBridge()
        
        self.persistent.connections.append(server)
        self.persistent._save()

        self.server.tellraw(At.AllPlayers, text.green(f"Connected to {server}"))


    def disconnect(self, server: str):
        
        if server not in self.persistent.connections:
            raise ServerDoesntExist()
        
        self.persistent.connections.remove(server)
        self.persistent._save()

        self.server.tellraw(At.AllPlayers, text.red(f"Disconnected from {server}"))
        

    @plugins.event(event=Event.PlayerJoin)
    def on_player_join(self, ctx: Context):
        
        msg = f"[{self.server.name}] <{ctx.player}> joined the game"
        self._server_broadcast(msg)

    
    @plugins.event(event=Event.PlayerLeft)
    def on_player_left(self, ctx: Context):
        
        msg = f"[{self.server.name}] <{ctx.player}> left the game"
        self._server_broadcast(msg)

    
    @plugins.event(event=Event.PlayerChat)
    def on_player_chat(self, ctx: Context):
        
        msg = f"[{self.server.name}] <{ctx.player}> {ctx.message}"
        self._server_broadcast(msg)

    
    @plugins.event(event=Event.PlayerDeath)
    def on_player_death(self, ctx: Context):
        
        msg = f"[{self.server.name}] {ctx.death_message}"
        self._server_broadcast(msg)


    @plugins.event(event=Event.ServerStart)
    def on_server_start(self, ctx: Context):
        
        msg = f"[{self.server.name}] server started!"
        self._server_broadcast(msg)


    @plugins.event(event=Event.ServerStop)
    def on_server_stop(self, ctx: Context):
        
        msg = f"[{self.server.name}] stopping the server!"
        self._server_broadcast(msg)

        for plg in self._get_plugin_instances():
            plg.disconnect(self.server.name)

    
    def _server_broadcast(self, message: Message):
        """
        Sends the given message to all the connected server
        """

        for plg in self._get_plugin_instances():
            plg._on_message(message)

        if self.__discord_enabled is True:

            if type(message) is not str:
                message = message.plain_text

            self.__discord_ext.send_message(self.config.bridge_channel, message)


    def _on_message(self, message: Message):
        
        if type(message) is str:
            message = text.Text(message)
        
        self.server.tellraw(At.AllPlayers, message.gray())
        

    def _on_discord_message(self, message: "discord.Message"):
        
        msg = f"[Discord] <{message.author}> {message.content}"
        
        self._on_message(text.Text(msg))