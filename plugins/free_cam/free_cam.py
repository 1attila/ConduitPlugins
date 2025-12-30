from typing import List
import copy

from mconduit import plugins, text, Context, Event, Dimension, Player


class BackupAlreadyExist(Exception):
    ...

class BackupDoesntExist(Exception):
    ...


class Persistent(plugins.Persistent):
    players: dict = {}
    backups: dict = {}


class Config(plugins.Config):
    prefixes: List[str] = ["r"]


class FreeCam(plugins.Plugin[Config, Persistent]):
    """
    Equivalent to /cs
    """

    
    freecam = plugins.Command.group(
        name="freecam",
        aliases=["fc"],
        checks=[plugins.check_perms(plugins.Permission.Helper)]
    )

    
    def save_pos(self, backup_name: str):
        """
        This must be called only when you took a backup that you migth restore.

        This is done because if a backup is taken with a player in spectator and then the same player goes back in survival the plugin delete it's old position, as normal.
        If the backup is restored tho, the player will be in spectator and it's old position removed, trapping him in spectator!
        """

        if backup_name in self.persistent.backups.keys():
            raise BackupAlreadyExist()
        
        self.persistent.backups[backup_name] = copy.copy(self.persistent.players)
        self.persistent._save()


    def restore_pos(self, backup_name: str):
        """
        This must be called only when a backup is restored.

        This is done because if a backup is taken with a player in spectator and then the same player goes back in survival the plugin delete it's old position, as normal.
        If the backup is restored tho, the player will be in spectator and it's old position removed, trapping him in spectator!
        """

        if backup_name not in self.persistent.backups.keys():
            raise BackupDoesntExist()

        self.persistent.players = copy.copy(self.persistent.backups[backup_name])
        self.persistent._save()

    
    def delete_pos(self, backup_name: str):
        """
        This must be called only when a backup is deleted and you also saved the freecam pos
        """

        if backup_name not in self.persistent.backups.keys():
            raise BackupDoesntExist()
        
        self.persistent.backups.pop(backup_name)
        self.persistent._save()

    
    @freecam.command
    def save(self, ctx: Context, backup_name: str):
        """
        Saves the current freecam positions for the given backup
        """

        try:
            self.save_pos(backup_name)

        except Exception as e:
            ctx.error(e)
            return

        ctx.success(f"Positions sucesfully saved for `{backup_name}`")

    
    @freecam.command(checks=[plugins.check_perms(plugins.Permission.Helper)])
    def restore(self, ctx: Context, backup_name: str):
        """
        Restore the saved freecam position from a given backup
        """

        try:
            self.restore_pos(backup_name)
        
        except Exception as e:
            ctx.error(e)
            return

        ctx.success(f"Positions sucesfully restored from `{backup_name}`")

    
    @freecam.command(checks=[plugins.check_perms(plugins.Permission.Helper)])
    def delete(self, ctx: Context, backup_name: str):
        """
        Delete the saved freecam positions of a given backup
        """

        try:
            self.delete_pos(backup_name)

        except Exception as e:
            ctx.error(e)
            return

        ctx.success(f"Sucesfully deleted positions for `{backup_name}`")


    @plugins.command
    def spec(self, ctx: Context, player: str):
        """
        Put the player who invoked the command in freecam and teleports it to the given player
        """

        if ctx.player.name in self.persistent.players:

            err = text.red("You are already in freecam!")
            self.server.execute(f"/title {ctx.player} actiobar {err}")
            return

        self.join_freecam(ctx)

        player = Player(player, self.server)
        self.server.execute(f"/execute in {player.dimension} run tp {ctx.player} {player.pos}")


    def join_freecam(self, ctx: Context):

        player = ctx.player
        
        self.persistent.players[player.name] = (
            player.gamemode.value,
            player.dimension.value,
            *player.pos.as_tuple(),
            *player.rotation.as_tuple()
        )
        self.persistent._save()

        self.server.execute(f"/gamemode spectator {player.name}")

        question = self.make_exit_text(ctx)

        ctx.reply(question + " " + self.add_waypoint(f"{ctx.player.name}s freecam pos", *ctx.player.pos.as_tuple(), ctx.player.dimension.value))

        msg = text.dark_aqua("You have been put into spectator")
        self.server.execute(f"/title {player.name} actionbar {msg}")


    def exit_freecam(self, ctx: Context):

        player = ctx.player

        gamemode, dim, x, y, z, yaw, pitch = self.persistent.players[player.name]

        self.server.execute(f"/execute in {dim} run tp {player.name} {x} {y} {z} {yaw} {pitch}")
        self.server.execute(f"/gamemode {gamemode} {player.name}")

        msg = text.dark_aqua(f"You have been put into {gamemode}")
        self.server.execute(f"/title {player.name} actionbar {msg}")

        self.persistent.players.pop(player.name)
        self.persistent._save()

        def _join_freecam(c: Context):
            
            if c.player.name in self.persistent.players:
    
                err = text.red("You are already in freecam!")
                self.server.execute(f"/title {c.player} actionbar {err}")
                return
            
            self.join_freecam(c)

        question = text.button(
            "Join freecam",
            show_text="Click to put yourself in freecam again!",
            run_function=_join_freecam 
        ).dark_aqua()

        ctx.reply(question)

    
    def add_waypoint(
                     self,
                     name: str,
                     x: int,
                     y: int,
                     z: int,
                     dim: Dimension
        ) -> text.Text:
        """
        Creates a Json Text with the commands to add Xaeros, Voxel and Conduit waypoints 
        """

        x, y, z = int(x), int(y), int(z)

        if not isinstance(dim, str):
            dim = dim.value

        voxel_command = f"/newWaypoint x:{x} y:{y} z:{z} dim:{dim}"
        xaero_command = f"xaero_waypoint_add:{name}:{name[0]}:{x}:{y}:{z}:6:false:0:Internal_{dim}_waypoints"

        voxel_text = text.aqua("[+V]").underlined()
        voxel_text.hover(show_text=text.aqua("Voxel") + text.gray(" waypoint"))
        voxel_text.click(run_command=voxel_command)

        xaero_text = text.gold("[+X]").underlined()
        xaero_text.hover(show_text=text.gold("Xaero") + text.gray(" waypoint"))
        xaero_text.click(suggest_command=xaero_command)

        voxel_text += " "
        voxel_text += xaero_text

        waypoint = self.manager.get_plugin_named("waypoint")

        if waypoint is not None:

            waypoint_new = waypoint.get_command_named("waypoint", "new").fallback

            conduit_text = text.dark_aqua("[+W]").underlined()
            conduit_text.hover(show_text=text.dark_aqua("Conduit") + text.gray(" waypoint"))
            conduit_text.click(run_function=lambda ctx: waypoint_new(ctx, name, x, y, z))

            voxel_text += " "
            voxel_text += conduit_text

        return voxel_text
    

    def make_exit_text(self, player_name: str) -> text.Text:

        def _exit_freecam(c: Context):

            if c.player.name not in self.persistent.players:

                err = text.red(f"You are not in free-cam anymore!")
                self.server.execute(f"/title {c.player.name} actionbar {err}")
                return
                
            self.exit_freecam(c)

        question = text.button(
            "Exit freecam",
            show_text="Click to exit free-cam",
            run_function=_exit_freecam
        ).dark_aqua()

        return question
    

    @plugins.event(event=Event.PlayerJoin)
    def on_player_join(self, ctx: Context):

        if ctx.player.name in self.persistent.players:
            ctx.reply(self.make_exit_text(ctx.player.name))
    
    
    @plugins.event(event=Event.PlayerChat)
    def on_player_message(self, ctx: Context):

        if ctx.message.strip().lower() in self.config.prefixes:

            player = ctx.player
            
            if player.name in self.persistent.players.keys():
                self.exit_freecam(ctx)
            else:
                self.join_freecam(ctx)