import datetime
import io
import discord
import matplotlib
import matplotlib.pyplot as plt
from discord.ext import commands
from typing import Optional, Dict


class ChatStats(commands.Cog):

    @commands.command(aliases=['chatstats', 'chat stats'])
    async def chat_stats(self, context: commands.Context, days: Optional[int]):
        '''Display stats for this context. Optionally given # days back. Will look only look at most 10k messages
        Example: !chatstats 10 -> chat stats for the last 10 days
        '''

        async with context.typing():  # at least give some level of feedback
            counts: Dict[str, int] = {}

            days_back = datetime.datetime.now() - datetime.timedelta(days=days) if days else None

            async for message in context.history(limit=10_000, after=days_back, oldest_first=False).filter(lambda m: not m.author.bot):  #type: discord.Message
                counts[message.author.display_name] = counts.get(message.author.display_name, 0) + 1

            with plt.xkcd():
                fig, axs = plt.subplots()  # type: plt.Figure, plt.Axes
                # no need to plot zeros
                names = sorted((key for (key, value) in counts.items() if value > 0), key=lambda x: len(x))
                values = [counts[n] for n in names]

                axs.bar(names, values)
                title = f'Number of messages in #{context.channel.name}'
                if days_back:
                    axs.set_title(title + f'\nsince {days_back:%Y-%m-%d}')
                else:
                    axs.set_title(title)

                # formatting
                for label in axs.get_xticklabels():  # type: matplotlib.text.Text
                    label.set_rotation(45)
                    label.set_horizontalalignment('right')
                fig.tight_layout()

                buffer = io.BytesIO()
                fig.savefig(buffer, format='png')
                buffer.seek(0)

            await context.send(file=discord.File(buffer, filename='chatstats.png'))
