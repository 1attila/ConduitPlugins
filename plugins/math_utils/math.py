from mconduit import plugins, Context, Event, text

import simpleeval
import parse


class Persistent(plugins.Persistent):
    symbols: dict[str, str] = []


class Math(plugins.Plugin[None, Persistent]):
    """
    Math utils
    """


    math = plugins.Command.group(
        name="math",
        aliases=["m"]
    )

    
    def _migth_be_expression(self, message: str) -> bool:
        """
        Check if the message could be an expression to evaluate.

        This simply checks for operands and nothing else
        """

        return (
            message.__contains__("+") or
            message.__contains__("-") or
            message.__contains__("*") or
            message.__contains__("/")
        )
    

    @math.command
    def let(self, ctx: Context, expr: list[str]):
        """
        Assign a value to variable
        """

        expression = "".join(expr).replace(" ", "")

        parsed = parse.parse(r"{var}={value}", expression)

        if parsed:

            var = parsed["var"].strip()
            value = parsed["value"].strip()

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
            return

        ctx.reply(text.dark_aqua("Variables:"))

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
                return

            except Exception as e:
                ctx.error(e)
                return

        elif self._migth_be_expression(message):
            
            try:
                result = simpleeval.simple_eval(message, names=self.persistent.symbols)

                ctx.info(result)
            
            except Exception as e:
                pass