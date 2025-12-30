from typing import Optional, Literal
import datetime
import parse

from mconduit import plugins, text, Context


class InvalidInfo(Exception):
    ...

class InvalidDatetime(Exception):
    ...

class InvalidPriority(Exception):
    ...

class InvalidStatus(Exception):
    ...

Action = Literal["add-step", "remove-step", "modify-step", "set-status", "add-info", "remove-info", "set-priority"]
Priority = Literal["low", "medium", "high"]
Status = Literal["started", "on-hold", "designing"]
Info = Literal["just-added", "now-avaiable", "mats-only"]

PRIORITY = {
    "low": text.gray("low"),
    "medium": text.gold("medium"),
    "high": text.green("high")
}

STATUS = {
    "started": text.green("started"),
    "on-hold": text.gold("on-hold"),
    "designing": text.red("designing")
}

INFOS = {
    "just-added": text.aqua("🆕").hover("just added"),
    "now-avaiable": text.green("★").hover("now avaiable"),
    "mats-only": text.gold("💼").hover("mats collection required")
}

DISCORD_PRIORITY = {
    "low": "🔴",
    "medium": "🟡",
    "high": "🟢"
}

DISCORD_STATUS = {
    "started": "🟩",
    "on-hold": "🟨",
    "designing": "🟥"
}

DISCORD_INFOS = {
    "just-added": "🆕",
    "now-avaiable": "⭐",
    "mats-only": "💼"
}


def _datetime_from(time: str) -> datetime.datetime:

    parsed = parse.parse(r"{year}-{month}-{day} {hour}:{minute}:{second}", time)

    if not parsed:
        raise InvalidDatetime
        
    year = int(parsed["year"])
    month = int(parsed["month"])
    day = int(parsed["day"])
    hour = int(parsed["hour"])
    minute = int(parsed["minute"])
    second = int(parsed["second"])

    return datetime.datetime(year, month, day, hour, minute, second)


def _relative_time(time: str) -> str:

    time = _datetime_from(time)
    
    delta: datetime.timedelta = datetime.datetime.now() - time
    
    delta_in_hours = round(delta.total_seconds() / 3600, 2)
    delta_in_days = round(delta.total_seconds() / 86400, 2)
    delta_in_months = round(delta_in_days / 31, 2)

    if delta_in_months > 1:

        return f"{delta_in_months} months"
    
    if delta_in_days > 1:
        
        return f"{delta_in_days} days"
    
    return f"{delta_in_hours} hours"


def _display_field(f_name: str, f_data: dict) -> text.Text:

    msg = text.dark_aqua(f"[{f_name}] ").bold()
    
    if "priority" in f_data:

        priority = f_data["priority"]

        if priority not in PRIORITY:
            raise InvalidPriority

        msg += text.aqua("priority: ") + PRIORITY[priority].italic()

    if "status" in f_data:

        status = f_data["status"]

        if status not in STATUS:
            raise InvalidStatus
        
        if "priority" in f_data:
            msg += text.aqua(", ")
        
        msg += text.aqua("status: ") + STATUS[status].italic()
    
    if "other_infos" in f_data:

        infos = text.Text("")

        for i, info in enumerate(f_data["other_infos"]):
            
            infos += INFOS[info]
                        
            if i + 1 < len(f_data["other_infos"]):
                infos += text.dark_aqua(" • ")

        if len(infos) > 0:
            msg += text.dark_aqua(" • ") + infos
        
        return msg

    else:
        return msg


def _display_project(ctx: Context, p_name: str, p_data: dict) -> None:

    ctx.reply(_display_field(p_name, p_data))

    if len(p_data["steps"]) > 0:
        
        ctx.info("  • Steps:")

        for s_name, s_data in p_data["steps"].items():
            
            msg = text.gray("      • ")
            ctx.reply(msg + _display_field(s_name, s_data))


def _discord_timestamp(date: str) -> str:

    t = int(_datetime_from(date).timestamp())

    return f"<t:{t}:f>, <t:{t}:R>"


class Persistent(plugins.Persistent):
    projects: dict[str, dict] = {}
    completed: dict[str, str] = {}


class TodoList(plugins.Plugin[None, Persistent]):
    """
    Todo list manager
    """


    def on_load(self):

        self.persistent.get_or(
            "update_time", 
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        self._update(update_time=False)

    
    def _update(self, update_time: bool=True) -> None:
        """
        Updates the update_time
        """

        if update_time is True:
            self.persistent.update_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self._update_projects()
        
        if (
            self.manager.are_plugins_loaded("discord_ext") and
            self.persistent.has_item("discord_channel_id")
        ):

            self._update_discord_embed()
        else:
            print("[TODO] Couldnt update the discord message since discord_ext wasnt loaded or discord_channel_id wasnt specified")
        

    def _update_projects(self) -> None:
        """
        Updates the project order to make sure that projects follow this priority:

        - status
        - priority
        """
        
        ordered_projects = {}

        for status in ["started", "on-hold", "designing"]:

            for priority in ["high", "medium", "low"]:

                for p_name, p_data in self.persistent.projects.items():

                    if p_name in ordered_projects.keys():
                        continue

                    if (
                        p_data["status"] == status and
                        p_data["priority"] == priority
                    ):
                        ordered_projects[p_name] = p_data

        self.persistent.projects = ordered_projects

    
    def _generate_name(self, name: str, data: dict) -> str:
        """
        Format the name of a project/step like so:

        <name>, status: <status>, priority: <priority> • <other-infos>

        If something is not set, it's ignored
        """
        
        out = name

        if "status" in data and data["status"] in STATUS:

            out += ", status: " + data["status"] + " " + DISCORD_STATUS[data["status"]]

        if "priority" in data and data["priority"] in PRIORITY:

            out += ", priority: " + data["priority"] + " " + DISCORD_PRIORITY[data["priority"]]

        if "other_infos" in data:
        
            for info in data["other_infos"]:
                
                if info in INFOS:
                    out += " • " + DISCORD_INFOS[info]

        return out

    
    def _generate_project_desc(self, project: dict) -> str:
        """
        Generates project description to use in discord.Embed
        """
        
        if len(project["steps"]) > 0:
            
            out = "\u2800• steps:\n"

            for s_name, s_data in project["steps"].items():
                out += "\u2800\u2800• " + self._generate_name(s_name, s_data) + "\n"

            return out
        
        return ""
    

    def _generate_completed_embed(self) -> object:

        import discord

        embed = discord.Embed(
            title="COMPLETED",
            description=f"Updated: {_discord_timestamp(self.persistent.update_time)}"
        )

        for p_name, c_time in self.persistent.completed.items():

            embed.add_field(
                name=p_name,
                value=f"Completed: {_discord_timestamp(c_time)}",
                inline=False
            )

        return embed


    def _generate_todo_embed(self) -> object:

        import discord

        embed = discord.Embed(
            title="TODO-LIST",
            description=f"Updated: {_discord_timestamp(self.persistent.update_time)}"
        )

        for p_name, proj in self.persistent.projects.items():
                
            proj_name = self._generate_name(p_name, proj)
            proj_desc = self._generate_project_desc(proj)

            embed.add_field(
                name=proj_name,
                value=proj_desc,
                inline=False
            )

        return embed

    
    def _update_discord_embed(self):
        """
        Generates and updates the discord Embed
        """
        
        import discord

        completed_embed = self._generate_completed_embed()
        todo_embed = self._generate_todo_embed()

        channel_id = self.persistent.discord_channel_id
        message_id = self.persistent.discord_message_id
        discord_ext = self.manager.get_plugin_named("discord_ext")

        try:
            discord_ext.edit_message(channel_id, message_id, embeds=[completed_embed, todo_embed])
            return

        except discord.Forbidden:
            
            print("[TODO] Couldnt find the discord message, trying to make a new one")

            try:

                message_text = "# TODO-LIST\n\n"
                message_text += "## Legend:\n"
                message_text += "### Project status:\n"
                message_text += "🟩 **Started**: this can be done now and doesn't need any extra work.\n"
                message_text += "🟨 **On hold**: can be worked on soon but has prerequisite steps.\n"
                message_text += "🟥 **Designing**: needs to be designed/set up in creative before being done on smp.\n\n"
                message_text += "### Project priority: \n"
                message_text += "🟢 **High**: max priority, try to work on this first.\n"
                message_text += "🟡 **Medium**: can work on this but it's not the main priority.\n"
                message_text += "🔴 **Low**: kinda useless, avoid to work on this.\n\n"
                message_text += "### Project infos:\n"
                message_text += "💼 **Mats only**: this just needs materials gathered and can then be worked on.\n"
                message_text += "⭐ **Now avaiable**: this is now green when previously it wasn't.\n"
                message_text += "🆕 **Just added**: this was just added.\n\n"
                message_text += f"*Update this list in-game with ```{self.manager.command_prefix}todo``` or this to know how to use the commands: ```{self.manager.command_prefix}help todo_list```*"

                message = discord_ext.send_message(channel_id, message_text)
                discord_ext.edit_message(channel_id, message.id, embeds=[completed_embed, todo_embed])
                self.persistent.discord_message_id = message.id

            except Exception as e:
                print("[TODO] Unable to send the discord message:", e)


    @plugins.command
    def todo(self, ctx: Context, project: Optional[str]=None, completed: plugins.Flag=False):
        """
        Displays the full todo-list or a specific project status
        """

        if project is None:

            if completed is True:
                
                if len(self.persistent.completed) == 0:
                    ctx.error("No project has been completed yet!")
                    return
                
                msg = text.aqua("Completed projects: ")
                msg += text.gray("(updated: ")

                time = text.gray(self.persistent.update_time).italic()
                time.hover(_relative_time(self.persistent.update_time) + " ago")
                msg += time
                msg += text.gray(")")

                ctx.reply(msg)

                for c_proj, c_time in self.persistent.completed.items():
                    
                    proj_msg = text.aqua(f"• {c_proj}, completed: ")
                    proj_msg += text.gray(c_time).italic().hover(_relative_time(c_time) + " ago")
                    
                    ctx.reply(proj_msg)

            else:

                if len(self.persistent.projects) == 0:
                    ctx.error("Todo-list is empty!")
                    return

                msg = text.gold("Todo-list: ")
                msg += text.gray("(updated: ")

                time = text.gray(self.persistent.update_time).italic()
                time.hover(_relative_time(self.persistent.update_time) + " ago")

                msg += time
                msg += text.gray(")")

                ctx.reply(msg)

                for p_name, p_data in self.persistent.projects.items():
                    _display_project(ctx, p_name, p_data)

        else:

            if project not in self.persistent.projects:
                
                if completed is True:
                    
                    if project not in self.persistent.completed:
                        ctx.error("Project is neither in todo or completed list")
                    else:
                        time_msg = text.gray(c_time).italic().hover(_relative_time(c_time) + " ago")
                        ctx.reply(text.gray(f"• {c_proj}, completed: ") + time_msg)
                else:
                    ctx.error("Project is not in the todo list")
                return
            
            _display_project(ctx, project, self.persistent.projects[project])
    
    
    @todo.command
    def new(self,
            ctx: Context,
            project: str,
            status: Status="designing",
            priority: Priority="low",
            infos: list[Info]=["just-added"]
            ):
        """
        Creates a new project
        """

        if project in self.persistent.projects:
            ctx.error(f"Project already exists")
            return

        self.persistent.projects[project] = {
            "status": status,
            "priority": priority,
            "other_infos": ["just-added"],
            "steps": {}
        }

        if len(infos) > 0:

            for info in infos:

                if info in ["now-avaiable", "mats-only"]:
                    self.persistent.projects[project]["other_infos"].append(info)
                elif info == "just-added":
                    pass
                else:
                    raise InvalidInfo()
                
        self._update()

        ctx.success(f"Project {project} created sucesfully!")
                

    @todo.command
    def remove(self, ctx: Context, project: str, confirm: plugins.Flag):
        """
        Removes a project from the todo list
        """

        if project not in self.persistent.projects:
            ctx.error(f"Project does not exist")
            return
        
        if confirm is False:

            warn = f"{self.manager.command_prefix}todo remove <project> removes the project from the list without the possibility to recover it!"
            ctx.warn(warn)

            confirm_text = text.red("[Remove]").underlined()
            confirm_text.hover("Click to paste remove command")
            confirm_text.click(suggest_command=f"{self.manager.command_prefix} todo remove {project} --confirm")

            move = text.green("[Move to completed]").underlined()
            move.hover("Click to move the project to completed ones")
            move.click(run_function= lambda c: self._complete(ctx, project))

            ctx.server.tellraw(ctx.player.name, text.gold("What you want to do? ") + confirm_text + " or " + move)
            return

        self.persistent.projects.pop(project)
        self._update()

        ctx.success(f"Project `{project}` sucesfully removed")


    def _complete(self, ctx: Context, project: str):
        """
        Moves the project from the todo list to the completed ones
        """

        if project not in self.persistent.projects:
            ctx.error(f"Project does not exist")
            return
        
        if project in self.persistent.completed:
            ctx.error(f"Project is already in completed-projects")
            return

        self.persistent.completed[project] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.persistent.projects.pop(project)
        self._update()

        ctx.success(f"Sucesfully moved `{project}` into completed-projects")

    
    @todo.command
    def complete(self, ctx: Context, project: str):
        """
        Moves the project from the todo list to the completed ones
        """

        self._complete(ctx, project)


    def _add_step(self, ctx: Context, project: str, step: str):
        
        p_name = str(project)
        project = self.persistent.projects[project]

        if step in project["steps"]:
            ctx.error(f"Project `{p_name}` already has a step named `{step}`")
            return
        
        project["steps"][step] = {}
        self._update()

        ctx.success(f"Added step `{step}` to `{p_name}`")


    def _remove_step(self, ctx: Context, project: str, step: str):
        
        p_name = str(project)
        project = self.persistent.projects[project]

        if step not in project["steps"]:
            ctx.error(f"Project `{p_name}` doesnt have any step named `{step}`")
            return
        
        project["steps"].pop(step)
        self._update()

        ctx.success(f"Removed step `{step}` from `{p_name}`")


    def _modify_step(self,
                     ctx: Context,
                     project: str,
                     step: str,
                     action: Action,
                     value: str
                     ):
        
        p_name = str(project)
        project = self.persistent.projects[project]

        if step not in project["steps"]:
            ctx.error(f"Step {step} is not project steps")
            return
        
        s_name = str(step)
        step = project["steps"][step]
        
        match action:

            case "add-info":

                if value not in INFOS:
                    ctx.error("Invalid info")
                    return
        
                if value in step.get("other_infos", []):
                    ctx.warn("Info already set")
                    return
        
                step.setdefault("other_infos", []).append(value)
                self._update()

                ctx.success(f"Set info `{value}` for `{p_name}-{s_name}`")
                return
            
            case "remove-info":

                if value not in INFOS:
                    ctx.error("Invalid info")
                    return
        
                if value not in project.get("other_infos", []):
                    ctx.error(f"`{p_name}-{s_name}` doesnt have any info named `{value}`")
                    return
        
                step.get("other_infos", []).remove(value)
                self._update()

                ctx.success(f"Removed info `{value}` from `{p_name}-{s_name}`")
                return

            case "set-priority":

                if value not in PRIORITY:
                    ctx.error("Invalid priority")
                    return
                
                step.setdefault("priority", "")
        
                if value == step["priority"]:
                    ctx.warn("Priority already set")
                    return
        
                
                step["priority"] = value
                self._update()

                ctx.success(f"Set priority `{value}` for `{p_name}-{s_name}`")
                return

            case "set-status":

                if value not in STATUS:
                    ctx.error("Invalid status")
                    return

                step.setdefault("status", "")

                if value == step["status"]:
                    ctx.warn("Status already set")
                    return
        
                step["status"] = value
                self._update()

                ctx.success(f"Set status `{value}` for `{p_name}-{s_name}`")
                return

            case _:
                ctx.error("Invalid action")
    

    def _set_status(self, ctx: Context, project: str, status: str):
        
        p_name = str(project)
        project = self.persistent.projects[project]

        if status not in STATUS:
            ctx.error("Invalid status")
            return
        
        if status == project["status"]:
            ctx.warn("Status already set")
            return
        
        project["status"] = status
        self._update()

        ctx.success(f"Set status `{status}` for `{p_name}`")


    def _add_info(self, ctx: Context, project: str, info: str):
        
        p_name = str(project)
        project = self.persistent.projects[project]

        if info not in INFOS:
            ctx.error("Invalid info")
            return
        
        if info in project["other_infos"]:
            ctx.warn("Info already set")
            return
        
        project["other_infos"].append(info)
        self._update()

        ctx.success(f"Set info `{info}` for `{p_name}`")
    

    def _remove_info(self, ctx: Context, project: str, info: str):
        
        p_name = str(project)
        project = self.persistent.projects[project]

        if info not in INFOS:
            ctx.error("Invalid info")
            return
        
        if info not in project["other_infos"]:
            ctx.error(f"Project {p_name} doesnt have any info named `{info}`")
            return
        
        
        project["other_infos"].remove(info)
        self._update()

        ctx.success(f"Removed info `{info}` from `{p_name}`")
    

    def _set_priority(self, ctx: Context, project: str, priority: str):
        
        p_name = str(project)
        project = self.persistent.projects[project]

        if priority not in PRIORITY:
            ctx.error("Invalid priority")
            return
        
        if priority == project["priority"]:
            ctx.warn("Priority already set")
            return
        
        project["priority"] = priority
        self._update()

        ctx.success(f"Set priority `{priority}` for `{p_name}`")
    

    @todo.command
    def modify(self,
               ctx: Context,
               project: str,
               action: Action,
               args: list[str]
               ):
        
        if len(args) < 1:
            ctx.error("InsufficentParameters")
            return

        if project not in self.persistent.projects:
            ctx.error("Project not found")
            return
        
        match action:

            case "add-step":
                
                self._add_step(ctx, project, args[0])
                return

            case "remove-step":
                
                self._remove_step(ctx, project, args[0])
                return

            case "modify-step":
                
                if len(args) != 3:
                    ctx.error(f"Expected 3 parameters, got {len(args)}")
                    return
                
                self._modify_step(ctx, project, args[0], args[1], args[2])
                return

            case "set-status":
                
                self._set_status(ctx, project, args[0])
                return

            case "add-info":
                
                self._add_info(ctx, project, args[0])
                return

            case "remove-info":
                
                self._remove_info(ctx, project, args[0])
                return

            case "set-priority":
                
                self._set_priority(ctx, project, args[0])
                return

            case _:
                ctx.error("Invalid action")