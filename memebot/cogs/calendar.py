import logging
import bisect
import datetime
from dataclasses import dataclass
import math
from typing import List, Tuple
from discord.ext import commands


log = logging.getLogger('memebot')

# sputnik launch day
DAY_ZERO = datetime.datetime(1957, 10, 4, tzinfo=datetime.timezone.utc)

DAYS_IN_128_YEARS = 46_751
DAYS_IN_64_YEARS = 23_376

DAYS_IN_MONTH = 24
MONTHS = [
    'serpeius',
    'pescius',
    'ardillius',
    'lupulius',
    'orsius',
    'aragnius',
    'leonius',
    'gattorius',
    'pollius',
    'cuervius',
    'ballius',
    'pecorius',
    'cerdius',
    'alceius',
    'rattorious',
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

    def __str__(self) -> str:
        return f'{self.day} {MONTHS[self.month - 1].capitalize()}, {self.year} SA ({self.isoformat()})'

    def isoformat(self) -> str:
        return f'{self.year:04d}-{self.month:02d}-{self.day:02d}'


class Calendar(commands.Cog):

    def __init__(self) -> None:
        super().__init__()
        self.year_generator = iterate_years_from_zero()
        year_info = next(self.year_generator)
        self.years_list: List[YearSum] = [
            YearSum(
                year_info=year_info,
                running_sum=0,
            ),
        ]
        self.extend_until((datetime.datetime.now(tz=datetime.timezone.utc) - DAY_ZERO).days)
    
    @commands.command(aliases=['calendar', 'today'])
    async def calendar(self, ctx: commands.Context):
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        date = self.shitty_convert_date(now)
        await ctx.send(date.isoformat())

    def shitty_convert_date(self, date: datetime.datetime) -> GPDate:
        delta = date - DAY_ZERO
        self.extend_until(delta.days)

        # now binary search
        insert_index = bisect.bisect(self.years_list, delta.days, key=lambda x: x.running_sum)
        # good luck
        year_sum = self.years_list[insert_index - 1]

        # print('number of days since day zero', delta.days)

        day_in_year = delta.days - year_sum.running_sum

        # print('this is day', day_in_year, f'math: {delta.days} - {year_sum.running_sum}')

        months = 15 if year_sum.year_info.number_of_days == 360 else 14
        month = math.floor(day_in_year / DAYS_IN_MONTH)

        # print('month is', month, 'out of', months, 'months this year.')
        # print(f'calculation steps math: floor({day_in_year} / {DAYS_IN_MONTH})')

        day = day_in_year - (month * DAYS_IN_MONTH)

        # print('day is', day)
        # print(f'calculation for day: {day_in_year} - ({month} * {DAYS_IN_MONTH})')

        return GPDate(
            year=year_sum.year_info.year,
            month=month,
            day=day,
        )

    def extend_until(self, days_since_zero: int):
        if days_since_zero <= 0:
            return
        if days_since_zero <= self.years_list[-1].running_sum:
            return
        for year_info in self.year_generator:
            previous_entry = self.years_list[-1]
            # new_running_sum = previous_entry.running_sum + year_info.number_of_days
            new_running_sum = previous_entry.running_sum + previous_entry.year_info.number_of_days

            # leap_str = ''
            # if year_info.number_of_days != 360:
            #     leap_str = f'. this is a leap year with {year_info.number_of_days} days!'
            # print(f'year {year_info.year}{leap_str}. there have been {new_running_sum} days at the beginning of this year')

            self.years_list.append(YearSum(
                year_info=year_info,
                running_sum=new_running_sum,
            ))
            if new_running_sum >= days_since_zero:
                break

    # def convert_date(date: datetime.datetime) -> datetime.date:
    #     delta = date - DAY_ZERO

    #     delta.days / 365

    #     longspans = math.floor(delta.days / DAYS_IN_128_YEARS)
    #     shortspans = math.floor((delta.days - (longspans * DAYS_IN_128_YEARS)) / DAYS_IN_64_YEARS)
    #     regular_years = (delta.days - (longspans * DAYS_IN_128_YEARS) - (shortspans * DAYS_IN_64_YEARS)) / 360

    #     year = ((longspans * DAYS_IN_128_YEARS)
    #         + (shortspans * DAYS_IN_64_YEARS)
    #         + math.floor(regular_years))
        
    #     days_in_year = 360
    #     if year != 0 and year % 64 == 0:
    #         days_in_year = 335 if year % 128 == 0 else 336

    #     month = regular_years % days_in_year


def iterate_years_from_zero():
    year = 0
    while True:
        yield YearInfo(
            year=year,
            number_of_days=360,
        )

        if year != 0 and year % 64 == 0:
            yield YearInfo(
                year=year,
                number_of_days=335 if year % 128 == 0 else 336
            )

        year += 1

