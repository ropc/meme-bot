import datetime
import io
import discord
import matplotlib
import matplotlib.pyplot as plt
from discord.ext import commands
from typing import Optional, Dict


class ChatStats(commands.Cog):

    @commands.command(aliases=['chatstats', 'chat stats'])
    async def chat_stats(self, context: commands.Context, days: Optional[int], input_channel: Optional[discord.TextChannel]):
        '''Display stats for this context. Optionally given # days back. Will look only look at up to 1k messages
        if no days argument given. Will look at up to 10k messages if days argument is given.
        Example: !chatstats 10 #general -> chat stats for the last 10 days in #general
        '''

        async with context.typing():  # at least give some level of feedback
            counts: Dict[str, int] = {}

            since_date = datetime.datetime.utcnow() - datetime.timedelta(days=days) if days else None
            limit = 10_000 if days else 1_000  # more accurate if days param is given

            channel = input_channel if input_channel else context.channel

            async for message in channel.history(limit=limit, after=since_date, oldest_first=False):  #type: discord.Message
                if message.author.bot:
                    continue
                counts[message.author.display_name] = counts.get(message.author.display_name, 0) + 1

            with plt.xkcd():
                fig, axs = plt.subplots()

                names = sorted(counts.keys(), key=lambda x: len(x))
                values = [counts[n] for n in names]

                axs.bar(names, values)
                # DM channels don't have a name attribute
                channel_name = f'#{channel.name}' if hasattr(channel, 'name') else 'this channel'
                title = f'Number of messages in {channel_name}'
                if since_date:
                    # context.history() expects timezone-naive datetime, but want to show timezone here
                    axs.set_title(title + f'\nsince {since_date.replace(tzinfo=datetime.timezone.utc):%Y-%m-%d %H:%M:%S %Z}')
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
