from typing import List
import copy

from mconduit import plugins, text, Context, Event


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

    
    @plugins.event(event=Event.PlayerChat)
    def on_player_message(self, ctx: Context):

        try:
            if ctx.message.strip().lower() in self.config.prefixes:

                player = ctx.player
            
                if player.name in self.persistent.players.keys():

                    gamemode, dim, x, y, z, yaw, pitch = self.persistent.players[player.name]

                    self.server.execute(f"/execute in {dim} run tp {player.name} {x} {y} {z} {yaw} {pitch}")
                    self.server.execute(f"/gamemode {gamemode} {player.name}")

                    msg = text.aqua(f"You have been put into {gamemode}")
                    self.server.execute(f"/title {player.name} actionbar {msg}")

                    self.persistent.players.pop(player.name)
                    self.persistent._save()

                else:
                    self.persistent.players[player.name] = (
                        player.gamemode.value,
                        player.dimension.value,
                        *player.pos.as_tuple(),
                        *player.rotation.as_tuple()
                    )

                    self.persistent._save()

                    self.server.execute(f"/gamemode spectator {player.name}")

                    ctx.reply(text.aqua("[FreeCam] Click here to back").hover(
                        show_text=str(player.pos.round(1))).click(
                        run_command=f"/execute if entity @a[name={player.name}, gamemode=spectator] run execute in {player.dimension.value} run tp {player.name} {player.pos}")
                    )

                    msg = text.aqua("You have been put into spectator")
                    self.server.execute(f"/title {player.name} actionbar {msg}")

        except Exception as e:
            ctx.error(e)