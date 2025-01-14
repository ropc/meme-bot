import logging
import bisect
import datetime
import collections
import math
import dateparser
from dataclasses import dataclass
from typing import Deque, Optional
from discord.ext import commands


log = logging.getLogger('memebot')

# sputnik launch day
DAY_ONE = datetime.datetime(1957, 10, 4, tzinfo=datetime.timezone.utc)

DAYS_IN_128_YEARS = 46_751
DAYS_IN_64_YEARS = 23_376

DAYS_IN_MONTH = 24
STANDARD_MONTHS = [
    'serpeius',
    'pescius',
    'ardillius',
    'lupulius',
    'orsius',
    'aragnius',
    'leonius',
    'gattorius',
    'pollius',
    'ballius',
    'cuervius',
    'pecorius',
    'cerdius',
    'alceius',
    'rattorious',
]
SUPPLEMENTAL_MONTHS = [
    'orzius',
    'bulgurius',
    'maisius',
    'farroius',
    'miglius',
    'granius',
    'avenius',
    'risius',
    'segalius',
    'sorgius',
    'teffius',
    'triticius',
    'saracenius',
    'amarantius',
]

DISPLAY_TIMEZONES = ['US/Eastern']


@dataclass
class YearInfo:
    year: int
    number_of_days: int

@dataclass
class YearSum:
    year_info: YearInfo
    running_sum: int  # THIS IS NOT INCLUSIVE OF THE NUMBER OF DAYS IN CURRENT YEAR

@dataclass
class GPDate:
    year: int
    month: int
    day: int
    year_info: YearInfo

    def __str__(self) -> str:
        month_table = STANDARD_MONTHS if self.year_info.number_of_days == 360 else SUPPLEMENTAL_MONTHS
        year_str = str(self.year) if self.year_info.number_of_days == 360 else f'{self.year}S'
        return f'{self.day} {month_table[self.month - 1].capitalize()}, {year_str} SA ({self.isoformat()})'

    def isoformat(self) -> str:
        year_symbol = 'N' if self.year_info.number_of_days == 360 else 'S'
        return f'{self.year:04d}{year_symbol}-{self.month:02d}-{self.day:02d}'


class Calendar(commands.Cog):

    def __init__(self) -> None:
        super().__init__()
        self.future_year_generator = iterate_future_years_from_zero()
        self.past_year_generator = iterate_past_years_before_zero()
        year_info = next(self.future_year_generator)
        self.years_list: Deque[YearSum] = collections.deque()
        self.years_list.append(
            YearSum(
                year_info=year_info,
                running_sum=0,
            )
        )
        self.extend_until((datetime.datetime.now(tz=datetime.timezone.utc) - DAY_ONE).days)

    ''' Today's date in Gugliotta-Pacheco Concordat'''
    @commands.command()
    async def today(self, ctx: commands.Context):
        return await self.date(ctx, datetime.datetime.utcnow().strftime('%Y-%m-%d'))

    ''' Convert a date to the Gugliotta-Pacheco Concordat.
    Example: !date 2023-10-16 -> 22 Rattorious, 66 SA (0066N-00-22)
    '''
    @commands.command()
    async def date(self, ctx: commands.Context, date_str: str):
        date = dateparser.parse(date_str, settings={
            'TIMEZONE': 'UTC',
            'RETURN_AS_TIMEZONE_AWARE': True,
        })
        if not date:
            await ctx.reply(f"couldn't read this date. try YYYY-MM-DD")
            return

        log.info(f'received date {date_str}, parsed as {date}')

        if abs(date - DAY_ONE) > datetime.timedelta(days=365 * 1e4):
            await ctx.send("date too far from now, i don't feel like calculating it")
            return

        gp_date = self.convert_date(date)
        await ctx.send(str(gp_date))

    def convert_date(self, date: datetime.datetime) -> GPDate:
        delta = date - DAY_ONE
        self.extend_until(delta.days)

        # now binary search
        insert_index = bisect.bisect(self.years_list, delta.days, key=lambda x: x.running_sum)
        # good luck
        year_sum = self.years_list[insert_index - 1]

        log.debug(f'number of days since day zero: {delta.days} for {date.isoformat()}')
        day_in_year = delta.days - year_sum.running_sum
        log.debug(f'this is day {day_in_year}. math: {delta.days} - {year_sum.running_sum}')

        month = math.floor(day_in_year / DAYS_IN_MONTH) + 1
        log.debug(f'month is {month}. math: floor({day_in_year} / {DAYS_IN_MONTH})')

        day = day_in_year - ((month - 1) * DAYS_IN_MONTH)

        log.debug(f'day is {day}. math: {day_in_year} - (({month} - 1) * {DAYS_IN_MONTH})')
        log.debug(f'final values: year={year_sum.year_info.year}, month={month}, day={day}')

        return GPDate(
            year=year_sum.year_info.year,
            month=month,
            day=day,
            year_info=year_sum.year_info,
        )

    def extend_until(self, days_since_zero: int):
        if days_since_zero > 0:
            self._extend_future(days_since_zero)
        else:
            self._extend_past(days_since_zero)

    def _extend_future(self, days_since_zero: int):
        if days_since_zero <= 0:
            return
        if days_since_zero <= self.years_list[-1].running_sum:
            return
        for year_info in self.future_year_generator:
            previous_entry = self.years_list[-1]
            # new_running_sum = previous_entry.running_sum + year_info.number_of_days
            new_running_sum = previous_entry.running_sum + previous_entry.year_info.number_of_days

            leap_str = ''
            if year_info.number_of_days != 360:
                leap_str = f'. this is a leap year with {year_info.number_of_days} days!'
            print(f'year {year_info.year}{leap_str}. there have been {new_running_sum} days at the beginning of this year')

            self.years_list.append(YearSum(
                year_info=year_info,
                running_sum=new_running_sum,
            ))
            if new_running_sum >= days_since_zero:
                break

    def _extend_past(self, days_since_zero: int):
        if days_since_zero >= 0:
            return
        if days_since_zero >= self.years_list[0].running_sum:
            return
        for year_info in self.past_year_generator:
            previous_entry = self.years_list[0]
            new_running_sum = previous_entry.running_sum - previous_entry.year_info.number_of_days

            leap_str = ''
            if year_info.number_of_days != 360:
                leap_str = f'. this is a leap year with {year_info.number_of_days} days!'
            print(f'year {year_info.year}{leap_str}. there have been {new_running_sum} days at the beginning of this year')

            self.years_list.appendleft(YearSum(
                year_info=year_info,
                running_sum=new_running_sum,
            ))
            if new_running_sum <= days_since_zero:
                break


def iterate_future_years_from_zero():
    year = 0
    while True:
        yield YearInfo(
            year=year,
            number_of_days=360,
        )

        if year != 0 and year % 64 == 0:
            yield YearInfo(
                year=year,
                number_of_days=336 if year % 128 == 0 else 335
            )

        year += 1


def iterate_past_years_before_zero():
    year = -1
    yield YearInfo(
        year=year,
        number_of_days=336,
    )
    while True:
        if year % 64 == 0:
            yield YearInfo(
                year=year,
                number_of_days=336 if year % 128 == 0 else 335
            )

        yield YearInfo(
            year=year,
            number_of_days=360,
        )

        year -= 1

