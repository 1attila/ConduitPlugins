from mconduit import plugins, Context, Event, text

import simpleeval
import parse


class Math(plugins.Plugin):
    """
    Math utils
    """


    math = plugins.Command.group(
        name="math",
        aliases=["m"]
    )


    def __init__(self, metadata, manager, lang) -> "Math":
        
        super().__init__(metadata, manager, lang)

        try:
            self.persistent.symbols
        except Exception as e:
            self.persistent.symbols = {}


    @math.command
    def let(self, ctx: Context, expr: list[str]):
        """
        Assign a value to variable
        """

        expression = "".join(expr).replace(" ", "")

        parsed = parse.parse(r"{var}={value}", expression)

        if parsed:

            var = parsed["var"]
            value = parsed["value"]

            try:
                value = float(value)
            except Exception as e:
                raise e

            if var.isdigit():
                ctx.error(f"Value `{var}` cant be a digit!")
                return
            
            self.persistent.symbols[var] = value
            self.persistent._save()

            ctx.success(f"Sucesfully assigned {var}={value}!")
            return
        
        ctx.error(f"`{expression}` is not a valid assignment!")


    @math.command(aliases=["lv"])
    def variables(self, ctx: Context):
        """
        Display all the variables used
        """

        if len(self.persistent.symbols.keys()) < 1:
            ctx.warn("There are no symbols!")

        ctx.reply(text.aqua("Variables:"))

        for name, value in self.persistent.symbols.items():
            ctx.info(f"{name}={value}")
    

    @plugins.event(event=Event.PlayerChat)
    def on_player_chat(self, ctx: Context):
        
        message = ctx.message.strip()

        if message.startswith("=="):
            
            try:
                expression = message[2:].strip()

                result = simpleeval.simple_eval(expression, names=self.persistent.symbols)

                ctx.info(result)

            except Exception as e:
                ctx.error(e)