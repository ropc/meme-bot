import asyncio
import datetime
import logging
import os.path
import re
import threading
import pickle
import dateparser
import dateutil.tz
import discord
from typing import Optional, Union, List
from discord.ext import commands
from pydantic import BaseModel

log = logging.getLogger('memebot')


class Reminder(BaseModel):
    user_id: int
    time: datetime.datetime
    message: str
    channel_id: int
    guild_id: Optional[int]  # if none, assume DMs


class ReminderCog(commands.Cog):

    def __init__(self, bot: commands.Bot, save_file_path: str):
        self.bot = bot
        self.regex_a = re.compile(r'(?:in|at|on)\s+(?P<time>.+)\s+(?:to|that|about)\s+(?P<message>.+)')
        self.regex_b = re.compile(r'(?:to|that|about)\s+(?P<message>.+)\s+(?:in|at|on)\s+(?P<time>.+)')
        self.reminders: List[Reminder] = []
        self.timer: Optional[threading.Timer] = None
        self.loop = asyncio.get_event_loop()
        self.save_file_path = save_file_path

    @commands.Cog.listener()
    async def on_ready(self):
        self.load_reminders()
        if len(self.reminders) > 0:
            self.set_timer(self.reminders[0])

    @commands.command(aliases=['remind me'])
    async def set_reminder(self, context: commands.Context, *, text: str):
        '''Set a reminder.
        Usage: "remind me (in|at|on) [time] (to|that) [message]" or
        "remind me (to|that) [message] (in|at|on) [time]"
        **Assumes 24-hour time in EST**, but you can explicity say am/pm
        or a different timezone
        '''
        async with context.typing():
            now = datetime.datetime.now(tz=dateutil.tz.gettz('US/Eastern'))
            match = self.regex_a.match(text) or self.regex_b.match(text)
            if not match:
                return await context.send('wrong format for reminder')

            match_dict = match.groupdict()
            user = context.author
            parser_settings = {
                'PREFER_DATES_FROM': 'future',
                'RELATIVE_BASE': now,
                'TIMEZONE': 'US/Eastern',
                'TO_TIMEZONE': 'UTC',
                'RETURN_AS_TIMEZONE_AWARE': True,
            }
            time = dateparser.parse(match_dict['time'], settings=parser_settings)
            message = match_dict['message']

            if not user or not time or not message:
                return await context.send('wrong format for reminder')

            if time < now:
                delta = now - time
                return await context.send(f"can't set reminder in the past {delta.seconds}s")

            reminder = Reminder(
                user_id=user.id,
                time=time,
                message=message,
                channel_id=context.channel.id,
                guild_id=context.guild.id if context.guild else None
            )

            if len(self.reminders) == 0 or (len(self.reminders) > 0 and self.reminders[0].time > reminder.time):
                self.set_timer(reminder)
            self.reminders.append(reminder)
            self.reminders.sort(key=lambda r: r.time)  # TODO: use a sorted data structure
            self.save_reminders()
            await context.reply(f"Reminder set at {format_time(reminder.time)}")

    @commands.command(aliases=['reminders'])
    async def list_reminders(self, context: commands.Context):
        '''List existing reminders'''
        async with context.typing():
            reminders = list(self.visible_reminders(context))
            if len(reminders) == 0:
                message = 'No reminders'
            else:
                unique_user_ids = set(r.user_id for r in reminders)
                unique_users = await asyncio.gather(*[self.get_user(user_id) for user_id in unique_user_ids])
                unique_users_dict = {user.id: user for user in unique_users}
                users = [unique_users_dict[r.user_id] for r in reminders]
                message = ('Reminders:\n'
                    + '\n'.join(format_reminder(i, user.display_name, reminder.message, reminder.time) for (i, (reminder, user)) in enumerate(zip(reminders, users))))
            await context.send(message)

    @commands.command(aliases=['cancel'])
    async def cancel_reminder(self, context: commands.Context, index: int):
        '''Cancel a reminder. Usage: !cancel <reminder number>'''
        async with context.typing():
            if len(self.reminders) <= index:
                return await context.send(f'No reminder at index {index}')

            if index == 0 and self.timer:
                self.timer.cancel()
                self.timer = None

            self.reminders.pop(index)
            self.save_reminders()

            if len(self.reminders) > 0 and index == 0:
                self.set_timer(self.reminders[0])

            await context.send(f'canceled reminder {index}')

    def timer_callback(self):
        if len(self.reminders) == 0:
            log.warn('timer callback called, but no reminders available')
            return

        reminder = self.reminders.pop(0)
        self.save_reminders()

        async def send_reminder():
            channel, user = await asyncio.gather(
                self.get_channel(reminder.channel_id),
                self.get_user(reminder.user_id)
            )
            if not channel or not user:
                log.error(f'missing channel [{channel}] or user[{user}] to send reminder')
            await channel.send(f"{user.mention}: {reminder.message}")

            now = datetime.datetime.now(tz=dateutil.tz.tzutc())
            error_in_seconds = (now - reminder.time).total_seconds()
            log.debug(f'sent reminder {reminder} with error {error_in_seconds}s')
            if abs(error_in_seconds) > 60:
                log.warn(f'reminder {reminder} has error >60s: {error_in_seconds}s')

        asyncio.run_coroutine_threadsafe(send_reminder(), self.loop)

        if len(self.reminders) > 0:
            self.set_timer(self.reminders[0])

    def set_timer(self, reminder: Reminder):
        if self.timer:
            self.timer.cancel()
        delay = max(reminder.time - datetime.datetime.now(tz=dateutil.tz.tzutc()), datetime.timedelta())
        log.debug(f'set timer for {delay.seconds}s')
        timer = threading.Timer(delay.seconds, self.timer_callback)
        self.timer = timer
        timer.start()

    def visible_reminders(self, context: commands.Context):
        if context.guild:
            return (r for r in self.reminders if r.guild_id == context.guild.id)
        else:
            return (r for r in self.reminders if r.user_id == context.author.id)

    async def get_user(self, user_id: int) -> Optional[discord.abc.User]:
        return self.bot.get_user(user_id) or await self.bot.fetch_user(user_id)

    async def get_channel(self, channel_id: int) -> Optional[discord.abc.Messageable]:
        return self.bot.get_channel(channel_id) or await self.bot.fetch_channel(channel_id)

    def load_reminders(self):
        if not os.path.isfile(self.save_file_path):
            log.warning(f"no reminders file at '{self.save_file_path}'")
            return
        with open(self.save_file_path, 'rb') as f:
            self.reminders = pickle.load(f)
        log.debug(f'loaded reminders: {self.reminders}')

    def save_reminders(self):
        with open(self.save_file_path, 'wb') as f:
            pickle.dump(self.reminders, f)
        log.debug(f'saved reminders: {self.reminders}')

def format_time(time: datetime.datetime) -> str:
    return time.astimezone(dateutil.tz.gettz('US/Eastern')).strftime('%H:%M:%S %b %d %Y %Z')

def format_reminder(index: int, username: str, message: str, time: datetime.datetime) -> str:
    formatted_time = format_time(time)
    return f'[{index}] - {username}: {message} _{formatted_time}_'
