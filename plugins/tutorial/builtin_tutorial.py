from mconduit.plugins import Plugin, Permission
from mconduit import text, Player


def commands(plg: Plugin, player: str):

    p = plg.manager.command_prefix

    tutorial = text.dark_aqua("The first thing you should know about conduit is how commands work!\n")
    tutorial += text.dark_aqua("To invoke a command type `")
    tutorial += text.dark_gray(p).bold()
    tutorial += text.dark_aqua("` followed by the name of the command you want to call.\n")
    tutorial += text.dark_aqua("Try it yourself! Type ")

    cmd = text.gold(f"{p}version").underlined().bold()
    cmd.hover("Click to paste in chat!")
    cmd.click(suggest_command=f"{p}version")

    tutorial += cmd
    tutorial += text.dark_aqua(" to print the version of conduit is running!")

    plg.server.tellraw(player, tutorial)


def commands_with_single_parameter(plg: Plugin, player: str):

    p = plg.manager.command_prefix

    tutorial = text.dark_aqua("Lets now invoke commands with parameters too!\n")
    tutorial += text.dark_aqua("They can be invoked like normal commands, followed by one ")
    tutorial += text.aqua("(or more)")
    tutorial += text.dark_aqua(" space and value of the parameter you want to pass\n")
    tutorial += text.dark_aqua("Parameters can be of many types:\n")
    tutorial += text.aqua(" • int: (integers) numbers with no decimal digits\n")
    tutorial += text.aqua(" • float: numbers with decimal digits \n")
    tutorial += text.aqua(" • str: normal text \n")
    tutorial += text.aqua(" • bool: true or false \n")
    tutorial += text.dark_aqua("These are just the most common, we will cover the rest later!\n")

    tutorial += "Try some commands yourself!\n"
    tutorial += text.dark_aqua(f"{p}perms <player_name>").underlined().bold()
    tutorial += " player_name is a string\n"
    tutorial += text.gray(f"{p}news <version>").underlined().bold() + " version is a string\n"

    plg.server.tellraw(player, tutorial)

    
def help(plg: Plugin, player: str):

    p = plg.manager.command_prefix

    cmd = text.gold(f"`{p}help`").underlined().bold()
    cmd.hover(show_text="Click to paste in chat!")
    cmd.click(suggest_command=f"{p}help")
        
    tutorial = text.dark_aqua("The ")
    tutorial += cmd
    tutorial += text.dark_aqua(" command gives you all the infos you need!\n")

    tutorial += text.dark_aqua("Lets see all its functions:\n")

    cmd1 = cmd + text.dark_aqua(": prints help on how to use it\n")

    cmd2 = text.gold(f"{p}help <command>").underlined().bold()
    cmd2 += text.dark_aqua(": prints the documentation of that command\n")

    cmd3 = text.gold(f"{p}help <plugin>").underlined().bold()
    cmd3 += text.dark_aqua(": prints all avaiable commands for that plugin\n")

    tutorial += cmd1 + cmd2 + cmd3

    cmd1 = cmd + "\n"
    cmd1.hover("Click to paste in chat!")
    cmd1.click(suggest_command=f"{p}help")

    cmd2 = text.gold(f"{p}help <command>\n").underlined().bold()
    cmd2.hover("Click to paste in chat!")
    cmd2.click(suggest_command=f"{p}help version")

    cmd3 = text.gold(f"{p}help <plugin>\n").underlined().bold()
    cmd3.hover("Click to paste in chat!")
    cmd3.click(suggest_command=f"{p}help builtin_plugin")

    cmds = text.dark_aqua("Try it yourself! Type: ")
    cmds += cmd1 + cmd2 + cmd3

    tutorial += cmds

    plg.server.tellraw(player, tutorial)


def group_commands(plg: Plugin, player: str):

    p = plg.manager.command_prefix

    tutorial = text.dark_aqua("There some commands that includes subcommands aswell like:\n")
    plugin = text.gray(f"{p}plugin").underlined()
    plugin.hover(show_text="Click to paste in chat!")
    plugin.click(suggest_command=f"{p}plugin")

    tutorial += plugin + " (empty)\n"

    n = (text.pixel_len(f"{p}plugin") - text.pixel_len("+")) / text.pixel_len("-")
    indentation = text.white("+" + int(n) * "-")

    p_list = text.gray("list").underlined()
    p_list.hover("Click to paste in chat!")
    p_list.click(suggest_command=f"{p}plugin list")

    tutorial += indentation + p_list + "\n"

    if Player(player, plg.server).permissions >= Permission.Helper:

        p_name = " <plugin-name>"

        p_load = text.gray("load").underlined()
        p_load.hover("Click to paste in chat!")
        p_load.click(suggest_command=f"{p}plugin load")
        p_load += p_name

        p_unload = text.gray("unload").underlined()
        p_unload.hover("Click to paste in chat!")
        p_unload.click(suggest_command=f"{p}plugin unload")
        p_unload += p_name

        p_reload = text.gray("reload").underlined()
        p_reload.hover("Click to paste in chat!")
        p_reload.click(suggest_command=f"{p}plugin reload")
        p_reload += p_name

        tutorial += indentation + p_load + "\n"
        tutorial += indentation + p_unload + "\n"
        tutorial += indentation + p_reload + "\n"

    tutorial += text.dark_aqua("To invoke them, just type the name of the subcommand after the command name, just like a parameter. ")
    tutorial += "Some commands only support subcommands while the `base` command is not\n"
    tutorial += "One of these commmands is "
    tutorial += plugin
    tutorial += text.dark_aqua(": if you invoke it alone it will raise ")
    tutorial += text.red("GroupCommandCalled")
    tutorial += text.dark_aqua(" since it cant be invoked alone!")

    plg.server.tellraw(player, tutorial)


def command_cache(plg: Plugin, player: str):
    """
    If you want to look to your latest 5 commands used you can simply type: {!!}(underlined)

    Same commands but with different arguments are considered different commands!
    If you havent typed any command it will print the builtin-commands you may want to use

    Try it yourself: {!!}(underlined)
    """

    p = plg.manager.command_prefix

    tutorial = text.dark_aqua("If you want to know your latest 5 commands invoked, simply type:")
    
    prefix = text.gold(p).underlined().bold().endl()
    prefix.hover("Click to paste in chat!")
    prefix.click(suggest_command=p)

    tutorial += prefix
    tutorial += text.dark_aqua("Same commands but different arguments are considered different commands!")

    plg.server.tellraw(player, tutorial)


def command_completion(plg: Plugin, player: str):
    """
    If you want to invoke a long command and dont want to type all of it or dont remember all its name,
    you can type {!!} followed by the partial name of the command and Conduit will make a list of possible choices
    
    Try yourself: {!!}p
    """


def multiple_arguments(plg: Plugin, player: str):
    """
    Commands might accept multiple arguments too.
    To input those, you just need to write them after the first argument, separated by one (or more) spaces!

    Example:
    {!!}help plugin load
    """

def multi_words(plg: Plugin, player: str):
    """
    Since every space separates some arguments, multi-world strings cannot be written as normal.

    If you want to pass multiple words togheter you have to sorround them in quotes!

    hello world x (red)
    "hello world" ok (green)
    """