import random
from discord.ext import commands

CARDS = [
    "(0) The Fool",
    "(1) The Magician",
    "(2) The High Priestess",
    "(3) The Emperor",
    "(4) The Empress",
    "(5) The Hierophant",
    "(6) The Lovers",
    "(7) The Chariot",
    "(8) Justice",
    "(9) The Hermit",
    "(10) Wheel of Fortune",
    "(11) Strength",
    "(12) The Hanged Man",
    "(13) Death",
    "(14) Temperance",
    "(15) The Devil",
    "(16) The Tower",
    "(17) The Star",
    "(18) The Moon",
    "(19) The Sun",
    "(20) Judgement",
    "(21) The World",
]

ORIENTATIONS = [
    "",
    ", inverted"
]

class TarotCard(commands.Cog):
    @commands.command()
    async def tarot(self, context: commands.Context):
        """deals random Tarot cards and their orientation."""
        
        cards = random.sample(CARDS, 3)
        await context.send(
            f"You are dealt **{cards[0] + random.choice(ORIENTATIONS)}**," +
            f" **{cards[1] + random.choice(ORIENTATIONS)}**," +
            f" and **{cards[2] + random.choice(ORIENTATIONS)}**."
        )



