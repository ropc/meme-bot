import random
from typing import Optional, Iterable
from discord.ext import commands


class RollDice(commands.Cog):

    def __init__(self, unlucky: Iterable[int]):
        self.unlucky = set(unlucky)

    @commands.command(aliases=['r', 'roll'])
    async def roll_dice(self, context: commands.Context, arg: Optional[str]):
        '''rolls dice. Example: !roll 5d6 (defaults to d20)'''
        if not arg:
            num_dice, num_sides = 1, 20
        else:
            num_dice, num_sides = [int(x if x else 1) for x in arg.split('d')]

        # soft limit. (2k - 16) hardcoded characters in message
        if num_dice * num_sides.bit_length() > 1984:
            return await context.send("I don't have all those dice")

        roll_func = _unlucky_roll if context.author.id in self.unlucky else _fair_roll

        raw_rolls = [roll_func(num_sides) for _ in range(num_dice)]
        total = sum(raw_rolls)

        if len(raw_rolls) > 1:
            formatted_rolls = ', '.join(str(r) for r in raw_rolls)
            message = f'Total: {total}, rolls: {formatted_rolls}'
        else:
            message = f'Total: {total}'

        if len(message) > 2000:  # discord has a 2k message limit
            return await context.send("I don't have all those dice")

        return await context.send(message)


def _unlucky_roll(num_sides: int):
    return max(random.randint(1, num_sides) - random.randint(0, num_sides//4), 1)

def _fair_roll(num_sides: int):
    return random.randint(1, num_sides)
