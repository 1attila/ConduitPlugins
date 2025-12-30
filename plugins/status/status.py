from typing import Optional, Iterable

from mconduit import plugins, text, utils, Context, Vec3d


class UnknownBlockType(Exception):
    """
    Block specified doesn't exist
    """

class InvalidCorners(Exception):
    """
    Thrown when more than 1 axis differs
    """


class Trace:
    """
    Utility class to create a trace
    """


    axis: str
    x1: int
    y1: int
    z1: int
    x2: int
    y2: int
    z2: int


    def __init__(self,
                 x1: int,
                 y1: int,
                 z1: int,
                 x2: int,
                 y2: int,
                 z2: int
                 ) -> "Trace":
        
        self.axis = "x" # Default
        self.x1 = x1
        self.y1 = y1
        self.z1 = z1
        self.x2 = x2
        self.y2 = y2
        self.z2 = z2


    def __iter__(self) -> Iterable[Vec3d]:
        
        if self.axis == "x":
            
            step = 1 if self.x2 > self.x1 else -1

            for x in range(self.x1, self.x2 + step, step):
                yield Vec3d(x, self.y1, self.z1)

        elif self.axis == "y":
            
            step = 1 if self.y2 > self.y1 else -1

            for y in range(self.y1, self.y2 + step, step):
                yield Vec3d(self.x1, y, self.z1)

        elif self.axis == "z":

            step = 1 if self.z2 > self.z1 else -1

            for z in range(self.z1, self.z2 + step, step):
                yield Vec3d(self.x1, self.y1, z)


class Persistent(plugins.Persistent):
    machines: dict = {}


class Status(plugins.Plugin[None, Persistent]):
    """
    Fetches the status of any machine
    """


    def _check_corners(self,
                       x1: int,
                       y1: int,
                       z1: int,
                       x2: int,
                       y2: int,
                       z2: int
                       ) -> None:
        """
        Asserts that coordinates differs only on a single axis 
        """

        count = 0

        if x1 != x2:
            count += 1

        if y1 != y2:
            count += 1

        if z1 != z2:
            count += 1

        if count != 1:
            raise InvalidCorners()


    @plugins.command(name="status", aliases=["stat"])
    def status(self, ctx: Context, machine: str, force_load: plugins.Flag):
        """
        Displays the status of the machine you specified
        """

        if machine not in self.persistent.machines:
            ctx.error(f"There is no machine named `{machine}`")
            return

        x1, y1, z1, x2, y2, z2, dim, block = self.persistent.machines[machine]
        trace = Trace(x1, y1, z1, x2, y2, z2)
        lenght = 0

        if force_load is True:

            if ctx.player.permissions < plugins.Permission.Helper:
                ctx.error("Invalid permissions to forceload!")
                return

            self.server.execute(f"/execute in {dim} run forceload add {x1} {z1} {x2} {z2}")

        if x1 != x2:
            trace.axis = "x"
            lenght = abs(x2 - x1)

            if y1 != y2 or z1 != z2:
                raise InvalidCorners()

        elif y1 != y2:
            trace.axis = "y"
            lenght = abs(y2 - y1)

            if x1 != x2 or z1 != z2:
                raise InvalidCorners()

        elif z1 != z2:
            trace.axis = "z"
            lenght = abs(z2 - z1)

            if x1 != x2 or y1 != y2:
                raise InvalidCorners()

        else:
            ctx.error(f"Corner1 its identical to Corner2!")
            return

        commands = []
        
        for i, pos in enumerate(trace):
            commands.append(f"/execute in {dim} if block {pos} {block}")

        responses = self.server.execute(commands)
        connection_flag = False
        unloaded_pos = []

        for i, pos in enumerate(trace):
            
            res = responses[i]

            if res == "":
                connection_flag = True

            elif res.startswith("Unknown block type"):
                raise UnknownBlockType()

            elif res.startswith("That position is not loaded"): # Sometimes its repeated twice
                unloaded_pos.append(utils.coords.chunk_coords(pos))

            elif res == "Test passed":

                perc = round(i / lenght * 100, 1)

                resp = text.dark_aqua(f"{machine} ")
                resp += text.aqua("is @ ")
                resp += text.gray(str(pos))
                resp += text.white(" (")
                resp += text.green(f"done: {i}")
                resp += text.dark_aqua(" • ")
                resp += text.gold(f"missing: {lenght - i}")
                resp += text.dark_aqua(f" • {perc}%")
                resp += text.white(")")
                ctx.reply(resp)

                if force_load is True:
                    self.server.execute(f"/execute in {dim} run forceload remove {x1} {z1} {x2} {z2}")

                return

        ctx.error("Unable to locate the machine")
        status = self.get_command_named("status")

        if len(unloaded_pos) > 0:
            
            unloaded_pos = set(unloaded_pos)
            msg = text.gold(f"{len(unloaded_pos)} chunks were unloaded ")

            chunk_list = " ".join(f"[{c.x} {c.z}]" for c in unloaded_pos)
            msg.hover(chunk_list)

            ask_msg = text.dark_aqua("[Use forceload]").underlined()
            ask_msg.hover("Click to fetch the result again!")

            ask_msg.click(run_function=lambda c: status.fallback(ctx=ctx, machine=machine, force_load=True))

            ctx.reply(msg + ask_msg)

        if connection_flag is True:

            msg = text.gold("Got some Rcon connection issues ")

            ask_msg = text.gold("[Attempt again]").underlined()
            ask_msg.hover("Click to fetch the result again!")

            ask_msg.click(run_function=lambda c: status.fallback(ctx=ctx, machine=machine, forceload=force_load))

            ctx.reply(msg + ask_msg)

        if force_load is True:
            self.server.execute(f"/execute in {dim} run forceload remove {x1} {z1} {x2} {z2}")
        

    @status.command
    def new(self,
            ctx: Context,
            name: str,
            x1: int, y1: int, z1: int,
            x2: int, y2: int, z2: int,
            block: str,
            dimension: Optional[str]=None
            ):
        """
        Sets a new status target
        """

        if name in self.persistent.machines.keys():
            
            ctx.error(f"Status target `{name}` already exist!")
            return

        self._check_corners(x1, y1, z1, x2, y2, z2)
        
        if dimension is None:
            dimension = ctx.player.dimension.value

        self.persistent.machines[name] = (
            x1, y1, z1,
            x2, y2, z2,
            dimension,
            block
        )
        self.persistent._save()

        ctx.success(f"New target status sucesfully set for `{name}`")


    @status.command(name="list")
    def _list(self, ctx: Context, all_infos: plugins.Flag):
        """
        Lists all the machines
        """

        if len(self.persistent.machines) == 0:
            ctx.warn("There is no machine yet!")
            return
        
        if all_infos is True:

            ctx.reply(text.aqua("Status list: "))

            for name, machine in self.persistent.machines.items():

                x1, y1, z1, x2, y2, z2, dim, _block = machine

                ctx.info(f"""•{name} ({dim}): ({x1}, {y1}, {z1}) --> ({x2}, {y2}, {z2})""")

            return
        
        resp = text.dark_aqua(f"Status list ({len(self.persistent.machines)}): ")
        resp += text.aqua(" • ".join(self.persistent.machines.keys()))

        ctx.reply(resp)


    @status.command
    def rename(self, ctx: Context, machine: str, new_name: str):
        """
        Renames the machine with the given name, if it's not used yet
        """

        if machine not in self.persistent.machines:
            ctx.error(f"There is no machine named `{machine}`!")
            return
        
        if new_name in self.persistent.machines:
            ctx.error(f"`{new_name}` is already used!")
            return

        self.persistent.machines[new_name] = self.persistent.machines[machine]
        self.persistent.machines.pop(machine)
        self.persistent._save()
    

    @status.command
    def delete(self, ctx: Context, machine: str):
        """
        Removes the machine from the list
        """

        if machine not in self.persistent.machines:
            ctx.error(f"There is no machine named `{machine}`")
            return
        
        self.persistent.machines.pop(machine)
        self.persistent._save()

        ctx.success(f"Machine `{machine}` has been removed from the status list")