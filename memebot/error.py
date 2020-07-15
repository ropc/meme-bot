from discord.ext import commands

class MemeBotError(commands.CommandError):
    '''First arg should be a string that will be sent as a response
    in error handler. Input will be quoted in the error message,
    so no need to include it in the string.

    Inherits from `discord.ext.commandsCommandError`
    '''
    pass

class MemeBotCheckError(commands.CheckFailure, MemeBotError):
    pass
