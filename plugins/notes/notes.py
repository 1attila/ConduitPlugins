from mconduit import plugins, text, Context


class Persistent(plugins.Persistent):
    notes: dict[str, str] = {}


class Notes(plugins.Plugin[None, Persistent]):
    """
    Simple notes manager
    """


    @plugins.command(aliases="nt")
    def notes(self, ctx: Context, name: str):
        """
        Prints the content of the note with the given name
        """

        if not name in self.persistent.notes:
            ctx.error(f"Note named `{name}` not found")
            return

        message = text.dark_aqua(name).bold().endl()
        message += text.gray(self.persistent.notes[name]).italic()

        ctx.reply(message)


    @notes.command
    def new(self, ctx: Context, name: str, content: str):
        """
        Creates a new note
        """

        if name in self.persistent.notes:
            ctx.error(f"Note named `{name}` already exists")
            return
        
        self.persistent.notes[name] = content
        
        ctx.success(f"Note `{name}` created sucesfully!")


    @notes.command
    def delete(self, ctx: Context, name: str):
        """
        Deletes an existing note
        """

        if not name in self.persistent.notes:
            ctx.error(f"Note named `{name}` not found")
            return
        
        self.persistent.notes.pop(name)

        ctx.success(f"Note `{name}` deleted sucesfully!")

    
    @notes.command
    def edit(self, ctx: Context, name: str, new_content: str):
        """
        Edits an existing note
        """

        if not name in self.persistent.notes:
            ctx.error(f"Note named `{name}` not found")
            return
        
        self.persistent.notes[name] = new_content

        ctx.success(f"Note `{name}` edited sucesfully!")

    
    @notes.command
    def append(self, ctx: Context, name: str, content: str):
        """
        Appends the given content at the end of the given note.

        Note: It doesnt go to a new line
        """

        if not name in self.persistent.notes:
            ctx.error(f"Note named `{name}` not found")
            return
        
        self.persistent.notes[name] += content

        ctx.success(f"Note `{name}` edited sucesfully!")

    
    @notes.command(name="list")
    def _list(self, ctx: Context):
        """
        Prints all the notes
        """

        if len(self.persistent.notes) == 0:
            ctx.warn("Notes are empty!")
            return
        
        notes = text.dark_aqua("Notes: ")
        notes += text.dark_aqua(" • ".join([note for note in self.persistent.notes.keys()]))

        ctx.reply(notes)