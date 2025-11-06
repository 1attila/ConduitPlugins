from typing import Optional, Iterable

from mconduit import plugins, text, Context


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


    def __iter__(self) -> Iterable[str]:
        
        if self.axis == "x":
            
            step = 1 if self.x2 > self.x1 else -1

            for x in range(self.x1, self.x2 + step, step):
                yield f"{x} {self.y1} {self.z1}"

        elif self.axis == "y":
            
            step = 1 if self.y2 > self.y1 else -1

            for y in range(self.y1, self.y2 + step, step):
                yield f"{self.x1} {y} {self.z1}"

        elif self.axis == "z":

            step = 1 if self.z2 > self.z1 else -1

            for z in range(self.z1, self.z2 + step, step):
                yield f"{self.x1} {self.y1} {z}"


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
    def status(self, ctx: Context, machine: str):
        """
        Displays the status of the machine you specified
        """

        if machine not in self.persistent.machines:
            ctx.error(f"There is no machine named `{machine}`")
            return

        x1, y1, z1, x2, y2, z2, dim, block = self.persistent.machines[machine]
        trace = Trace(x1, y1, z1, x2, y2, z2)
        lenght = 0

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

        connection_flag = False
        
        for i, pos in enumerate(trace):
            
            res = self.server.execute(f"/execute in {dim} if block {pos} {block}")

            if res is None:
                connection_flag = True

            if res.startswith("Unknown block type"):
                raise UnknownBlockType()

            if res != "Test failed":

                perc = i / lenght * 100
                
                ctx.warn(f"{machine} is at {pos} (done: {i} • missing: {lenght - i} • {perc}%)")
                return

        ctx.error("Unable to locate the machine")

        if connection_flag is True:

            msg = text.gold("Got some Rcon connection issues ")

            ask_msg = text.gold("[Attempt again]").underlined()
            ask_msg.hover("Click to fetch the result again!")

            ask_msg.click(run_function=lambda: self.status(ctx, machine))

            ctx.reply(msg + ask_msg)


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

        ctx.reply(text.aqua(f"""Status list: {", ".join(self.persistent.machines.keys())}"""))


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
    def remove(self, ctx: Context, machine: str):
        """
        Removes the machine from the list
        """

        if machine not in self.persistent.machines:
            ctx.error(f"There is no machine named `{machine}`")
            return
        
        self.persistent.machines.pop(machine)
        self.persistent._save()

        ctx.success(f"Machine `{machine}` has been removed from the status list")