from datetime import datetime, timedelta, timezone, tzinfo, date
from dateutil.relativedelta import relativedelta
from enum import Enum   
from typing import Tuple, Optional, Dict, Any, List, Union

from ovos_utils.time import now_local, to_local


class DurationResolution(Enum):
    TIMEDELTA = 0
    RELATIVEDELTA = 1
    RELATIVEDELTA_STRICT = 1
    RELATIVEDELTA_FALLBACK = 2
    RELATIVEDELTA_APPROXIMATE = 3
    TOTAL_SECONDS = 4
    TOTAL_MICROSECONDS = 5
    TOTAL_MILLISECONDS = 6
    TOTAL_MINUTES = 7
    TOTAL_HOURS = 8
    TOTAL_DAYS = 9
    TOTAL_WEEKS = 10
    TOTAL_MONTHS = 11
    TOTAL_YEARS = 12
    TOTAL_DECADES = 13
    TOTAL_CENTURIES = 14
    TOTAL_MILLENNIUMS = 15


class DateTimeResolution(Enum):
    # absolute units
    MICROSECOND = 0
    MILLISECOND = 1
    SECOND = 2
    MINUTE = 3
    HOUR = 4

    DAY = 5
    WEEKEND = 6
    WEEK = 7
    MONTH = 8
    YEAR = 9
    DECADE = 10
    CENTURY = 11
    MILLENNIUM = 12

    SEASON = 13
    SPRING = 14
    FALL = 15
    WINTER = 16
    SUMMER = 17

    # {unit} of {resolution}
    MICROSECOND_OF_MILLISECOND = 18
    MICROSECOND_OF_SECOND = 19
    MICROSECOND_OF_MINUTE = 20
    MICROSECOND_OF_HOUR = 21
    MICROSECOND_OF_DAY = 22
    MICROSECOND_OF_WEEKEND = 23
    MICROSECOND_OF_WEEK = 24
    MICROSECOND_OF_MONTH = 25
    MICROSECOND_OF_YEAR = 26
    MICROSECOND_OF_DECADE = 27
    MICROSECOND_OF_CENTURY = 28
    MICROSECOND_OF_MILLENNIUM = 29

    MICROSECOND_OF_SEASON = 30
    MICROSECOND_OF_SPRING = 31
    MICROSECOND_OF_FALL = 32
    MICROSECOND_OF_WINTER = 33
    MICROSECOND_OF_SUMMER = 34

    MICROSECOND_OF_REFERENCE = 35

    MILLISECOND_OF_SECOND = 36
    MILLISECOND_OF_MINUTE = 37
    MILLISECOND_OF_HOUR = 38
    MILLISECOND_OF_DAY = 39
    MILLISECOND_OF_WEEKEND = 40
    MILLISECOND_OF_WEEK = 41
    MILLISECOND_OF_MONTH = 42
    MILLISECOND_OF_YEAR = 43
    MILLISECOND_OF_DECADE = 44
    MILLISECOND_OF_CENTURY = 45
    MILLISECOND_OF_MILLENNIUM = 46

    MILLISECOND_OF_SEASON = 47
    MILLISECOND_OF_SPRING = 48
    MILLISECOND_OF_FALL = 49
    MILLISECOND_OF_WINTER = 50
    MILLISECOND_OF_SUMMER = 51

    MILLSECOND_OF_REFERENCE = 52

    SECOND_OF_MINUTE = 53
    SECOND_OF_HOUR = 54
    SECOND_OF_DAY = 55
    SECOND_OF_WEEKEND = 56
    SECOND_OF_WEEK = 57
    SECOND_OF_MONTH = 58
    SECOND_OF_YEAR = 59
    SECOND_OF_DECADE = 60
    SECOND_OF_CENTURY = 61
    SECOND_OF_MILLENNIUM = 62

    SECOND_OF_SEASON = 63
    SECOND_OF_SPRING = 64
    SECOND_OF_FALL = 65
    SECOND_OF_WINTER = 66
    SECOND_OF_SUMMER = 67

    SECOND_OF_REFERENCE = 68

    MINUTE_OF_HOUR = 69
    MINUTE_OF_DAY = 70
    MINUTE_OF_WEEKEND = 71
    MINUTE_OF_WEEK = 72
    MINUTE_OF_MONTH = 73
    MINUTE_OF_YEAR = 74
    MINUTE_OF_DECADE = 75
    MINUTE_OF_CENTURY = 76
    MINUTE_OF_MILLENNIUM = 77

    MINUTE_OF_SEASON = 78
    MINUTE_OF_SPRING = 79
    MINUTE_OF_FALL = 80
    MINUTE_OF_WINTER = 81
    MINUTE_OF_SUMMER = 82

    MINUTE_OF_REFERENCE = 83

    HOUR_OF_DAY = 84
    HOUR_OF_WEEKEND = 85
    HOUR_OF_WEEK = 86
    HOUR_OF_MONTH = 87
    HOUR_OF_YEAR = 88
    HOUR_OF_DECADE = 89
    HOUR_OF_CENTURY = 90
    HOUR_OF_MILLENNIUM = 91

    HOUR_OF_SEASON = 92
    HOUR_OF_SPRING = 93
    HOUR_OF_FALL = 94
    HOUR_OF_WINTER = 95
    HOUR_OF_SUMMER = 96

    HOUR_OF_REFERENCE = 97

    DAY_OF_WEEKEND = 98
    DAY_OF_WEEK = 99
    DAY_OF_MONTH = 100
    DAY_OF_YEAR = 101
    DAY_OF_DECADE = 102
    DAY_OF_CENTURY = 103
    DAY_OF_MILLENNIUM = 104

    DAY_OF_SEASON = 105
    DAY_OF_SPRING = 106
    DAY_OF_FALL = 107
    DAY_OF_WINTER = 108
    DAY_OF_SUMMER = 109

    DAY_OF_REFERENCE = 110

    WEEKEND_OF_MONTH = 111
    WEEKEND_OF_YEAR = 112
    WEEKEND_OF_DECADE = 113
    WEEKEND_OF_CENTURY = 114
    WEEKEND_OF_MILLENNIUM = 115

    WEEKEND_OF_SEASON = 116
    WEEKEND_OF_SPRING = 117
    WEEKEND_OF_FALL = 118
    WEEKEND_OF_WINTER = 119
    WEEKEND_OF_SUMMER = 120

    WEEKEND_OF_REFERENCE = 121

    WEEK_OF_MONTH = 122
    WEEK_OF_YEAR = 123
    WEEK_OF_CENTURY = 124
    WEEK_OF_DECADE = 125
    WEEK_OF_MILLENNIUM = 126

    WEEK_OF_SEASON = 127
    WEEK_OF_SPRING = 128
    WEEK_OF_FALL = 129
    WEEK_OF_WINTER = 130
    WEEK_OF_SUMMER = 131

    WEEK_OF_REFERENCE = 132

    MONTH_OF_YEAR = 133
    MONTH_OF_DECADE = 134
    MONTH_OF_CENTURY = 135
    MONTH_OF_MILLENNIUM = 136

    MONTH_OF_SEASON = 137
    MONTH_OF_SPRING = 138
    MONTH_OF_FALL = 139
    MONTH_OF_WINTER = 140
    MONTH_OF_SUMMER = 141

    MONTH_OF_REFERENCE = 142

    YEAR_OF_DECADE = 143
    YEAR_OF_CENTURY = 144
    YEAR_OF_MILLENNIUM = 145

    YEAR_OF_REFERENCE = 146

    DECADE_OF_CENTURY = 147
    DECADE_OF_MILLENNIUM = 148
    DECADE_OF_REFERENCE = 149

    CENTURY_OF_MILLENNIUM = 150
    CENTURY_OF_REFERENCE = 151

    MILLENNIUM_OF_REFERENCE = 152
    
    SEASON_OF_YEAR = 153
    SEASON_OF_DECADE = 154
    SEASON_OF_CENTURY = 155
    SEASON_OF_MILLENNIUM = 156

    SPRING_OF_YEAR = 157
    SPRING_OF_DECADE = 158
    SPRING_OF_CENTURY = 159
    SPRING_OF_MILLENNIUM = 160

    FALL_OF_YEAR = 161
    FALL_OF_DECADE = 162
    FALL_OF_CENTURY = 163
    FALL_OF_MILLENNIUM = 164

    WINTER_OF_YEAR = 165
    WINTER_OF_DECADE = 166
    WINTER_OF_CENTURY = 167
    WINTER_OF_MILLENNIUM = 168

    SUMMER_OF_YEAR = 169
    SUMMER_OF_DECADE = 170
    SUMMER_OF_CENTURY = 171
    SUMMER_OF_MILLENNIUM = 172

    # Special reference dates
    # number of days since 1 January 4713 BC, 12:00:00 (UTC).
    JULIAN = 681
    JULIAN_MICROSECOND = 173
    JULIAN_MILLISECOND = 174
    JULIAN_SECOND = 175
    JULIAN_MINUTE = 176
    JULIAN_HOUR = 177
    JULIAN_DAY = 178
    JULIAN_WEEK = 179
    JULIAN_WEEKEND = 180
    JULIAN_MONTH = 181
    JULIAN_YEAR = 182
    JULIAN_DECADE = 183
    JULIAN_CENTURY = 184
    JULIAN_MILLENNIUM = 185

    JULIAN_SEASON = 186
    JULIAN_SPRING = 187
    JULIAN_FALL = 188
    JULIAN_WINTER = 189
    JULIAN_SUMMER = 190

    # Julian day corrected for differences  in the Earth's position with
    # respect to the Sun.
    HELIOCENTRIC_JULIAN_MICROSECOND = 191
    HELIOCENTRIC_JULIAN_MILLISECOND = 192
    HELIOCENTRIC_JULIAN_SECOND = 193
    HELIOCENTRIC_JULIAN_MINUTE = 194
    HELIOCENTRIC_JULIAN_HOUR = 195
    HELIOCENTRIC_JULIAN_DAY = 196
    HELIOCENTRIC_JULIAN_WEEK = 197
    HELIOCENTRIC_JULIAN_WEEKEND = 198
    HELIOCENTRIC_JULIAN_MONTH = 199
    HELIOCENTRIC_JULIAN_YEAR = 200
    HELIOCENTRIC_JULIAN_DECADE = 201
    HELIOCENTRIC_JULIAN_CENTURY = 202
    HELIOCENTRIC_JULIAN_MILLENNIUM = 203

    HELIOCENTRIC_JULIAN_SEASON = 204
    HELIOCENTRIC_JULIAN_SPRING = 205
    HELIOCENTRIC_JULIAN_FALL = 206
    HELIOCENTRIC_JULIAN_WINTER = 207
    HELIOCENTRIC_JULIAN_SUMMER = 208

    # Julian day corrected for differences in the Earth's position with
    # respect to the barycentre of the Solar System.
    BARYCENTRIC__JULIAN_MICROSECOND = 209
    BARYCENTRIC__JULIAN_MILLISECOND = 210
    BARYCENTRIC__JULIAN_SECOND = 211
    BARYCENTRIC__JULIAN_MINUTE = 212
    BARYCENTRIC__JULIAN_HOUR = 213
    BARYCENTRIC_JULIAN_DAY = 214
    BARYCENTRIC_JULIAN_WEEK = 215
    BARYCENTRIC_JULIAN_WEEKEND = 216
    BARYCENTRIC_JULIAN_MONTH = 217
    BARYCENTRIC_JULIAN_YEAR = 218
    BARYCENTRIC_JULIAN_DECADE = 219
    BARYCENTRIC_JULIAN_CENTURY = 220
    BARYCENTRIC_JULIAN_MILLENNIUM = 221

    BARYCENTRIC_JULIAN_SEASON = 222
    BARYCENTRIC_JULIAN_SPRING = 223
    BARYCENTRIC_JULIAN_FALL = 224
    BARYCENTRIC_JULIAN_WINTER = 225
    BARYCENTRIC_JULIAN_SUMMER = 226

    # Unix time, number of seconds elapsed since 1 January 1970, 00:00:00 (
    # UTC).
    UNIX = 680
    UNIX_MICROSECOND = 227
    UNIX_MILLISECOND = 228
    UNIX_SECOND = 229
    UNIX_MINUTE = 230
    UNIX_HOUR = 231
    UNIX_DAY = 232
    UNIX_WEEK = 233
    UNIX_WEEKEND = 234
    UNIX_MONTH = 235
    UNIX_YEAR = 236
    UNIX_DECADE = 237
    UNIX_CENTURY = 238
    UNIX_MILLENNIUM = 239

    UNIX_SEASON = 240
    UNIX_SPRING = 241
    UNIX_FALL = 242
    UNIX_WINTER = 243
    UNIX_SUMMER = 244

    # Lilian date, number of days elapsed since the beginning of
    # the Gregorian Calendar on 15 October 1582.
    LILIAN = 682
    LILIAN_MICROSECOND = 245
    LILIAN_MILLISECOND = 246
    LILIAN_SECOND = 247
    LILIAN_MINUTE = 248
    LILIAN_HOUR = 249
    LILIAN_DAY = 250
    LILIAN_WEEK = 251
    LILIAN_WEEKEND = 252
    LILIAN_MONTH = 253
    LILIAN_YEAR = 254
    LILIAN_DECADE = 255
    LILIAN_CENTURY = 256
    LILIAN_MILLENNIUM = 257

    LILIAN_SEASON = 258
    LILIAN_SPRING = 259
    LILIAN_FALL = 260
    LILIAN_WINTER = 261
    LILIAN_SUMMER = 262

    # Holocene/Human Era s a year numbering system that adds exactly
    # 10,000 years to the currently dominant (AD/BC or CE/BCE) numbering scheme,
    # placing its first year near the beginning of the Holocene geological
    # epoch and the Neolithic Revolution
    HOLOCENE = 713
    HOLOCENE_MICROSECOND = 263
    HOLOCENE_MILLISECOND = 264
    HOLOCENE_SECOND = 265
    HOLOCENE_MINUTE = 266
    HOLOCENE_HOUR = 267
    HOLOCENE_DAY = 268
    HOLOCENE_WEEK = 269
    HOLOCENE_WEEKEND = 270
    HOLOCENE_MONTH = 271
    HOLOCENE_YEAR = 272
    HOLOCENE_DECADE = 273
    HOLOCENE_CENTURY = 274
    HOLOCENE_MILLENNIUM = 275

    HOLOCENE_SEASON = 276
    HOLOCENE_SPRING = 277
    HOLOCENE_FALL = 278
    HOLOCENE_WINTER = 279
    HOLOCENE_SUMMER = 280

    # Before Present (BP) years is a time scale used mainly in archaeology,
    # geology and other scientific disciplines to specify when events
    # occurred in the past. Because the "present" time changes, standard
    # practice is to use 1 January 1950 as the commencement date
    BEFORE_PRESENT = 679
    BEFORE_PRESENT_MICROSECOND = 281
    BEFORE_PRESENT_MILLISECOND = 282
    BEFORE_PRESENT_SECOND = 283
    BEFORE_PRESENT_MINUTE = 284
    BEFORE_PRESENT_HOUR = 285
    BEFORE_PRESENT_DAY = 286
    BEFORE_PRESENT_WEEK = 287
    BEFORE_PRESENT_WEEKEND = 288
    BEFORE_PRESENT_MONTH = 289
    BEFORE_PRESENT_YEAR = 290
    BEFORE_PRESENT_DECADE = 291
    BEFORE_PRESENT_CENTURY = 292
    BEFORE_PRESENT_MILLENNIUM = 293

    BEFORE_PRESENT_SEASON = 294
    BEFORE_PRESENT_SPRING = 295
    BEFORE_PRESENT_FALL = 296
    BEFORE_PRESENT_WINTER = 297
    BEFORE_PRESENT_SUMMER = 298

    # After the Development of Agriculture (ADA) is a system for
    # counting years forward from 8000 BCE, making 2020 the year 10020 ADA
    ADA = 714
    ADA_MICROSECOND = 299
    ADA_MILLISECOND = 300
    ADA_SECOND = 301
    ADA_MINUTE = 302
    ADA_HOUR = 303
    ADA_DAY = 304
    ADA_WEEK = 305
    ADA_WEEKEND = 306
    ADA_MONTH = 307
    ADA_YEAR = 308
    ADA_DECADE = 309
    ADA_CENTURY = 310
    ADA_MILLENNIUM = 311

    ADA_SEASON = 312
    ADA_SPRING = 313
    ADA_FALL = 314
    ADA_WINTER = 315
    ADA_SUMMER = 316

    # Alexandrian Era - 25 March 5493 BC
    ALEXANDRIAN_MICROSECOND = 317
    ALEXANDRIAN_MILLISECOND = 318
    ALEXANDRIAN_SECOND = 319
    ALEXANDRIAN_MINUTE = 320
    ALEXANDRIAN_HOUR = 321
    ALEXANDRIAN_DAY = 322
    ALEXANDRIAN_WEEK = 323
    ALEXANDRIAN_WEEKEND = 324
    ALEXANDRIAN_MONTH = 325
    ALEXANDRIAN_YEAR = 326
    ALEXANDRIAN_DECADE = 327
    ALEXANDRIAN_CENTURY = 328
    ALEXANDRIAN_MILLENNIUM = 329

    ALEXANDRIAN_SEASON = 330
    ALEXANDRIAN_SPRING = 331
    ALEXANDRIAN_FALL = 332
    ALEXANDRIAN_WINTER = 333
    ALEXANDRIAN_SUMMER = 334

    # "Creation Era of Constantinople" or "Era of the World"
    # September 1, 5509 BC
    CEC = 715
    CEC_MICROSECOND = 335
    CEC_MILLISECOND = 336
    CEC_SECOND = 337
    CEC_MINUTE = 338
    CEC_HOUR = 339
    CEC_DAY = 340
    CEC_WEEK = 341
    CEC_WEEKEND = 342
    CEC_MONTH = 343
    CEC_YEAR = 344
    CEC_DECADE = 345
    CEC_CENTURY = 346
    CEC_MILLENNIUM = 347

    CEC_SEASON = 348
    CEC_SPRING = 349
    CEC_FALL = 350
    CEC_WINTER = 351
    CEC_SUMMER = 352

    ### Everything bellow only for convenience

    # Rata Die, number of days elapsed since 1 January 1 in the proleptic
    # Gregorian calendar.
    RATADIE = 353
    RATADIE_MICROSECOND = 354
    RATADIE_MILLISECOND = 355
    RATADIE_SECOND = 356
    RATADIE_MINUTE = 357
    RATADIE_HOUR = 358
    RATADIE_DAY = 359
    RATADIE_WEEK = 360
    RATADIE_WEEKEND = 361
    RATADIE_MONTH = 362
    RATADIE_YEAR = 363
    RATADIE_DECADE = 364
    RATADIE_CENTURY = 365
    RATADIE_MILLENNIUM = 366

    RATADIE_SEASON = 367
    RATADIE_SPRING = 368
    RATADIE_FALL = 369
    RATADIE_WINTER = 370
    RATADIE_SUMMER = 371

    # CommonEra, since 1 January 1 in the proleptic Gregorian calendar.
    CE = DAY
    CE_MICROSECOND = MICROSECOND
    CE_MILLISECOND = MILLISECOND
    CE_SECOND = SECOND
    CE_MINUTE = MINUTE
    CE_HOUR = HOUR
    CE_DAY = DAY
    CE_WEEK = WEEK
    CE_WEEKEND = WEEKEND
    CE_MONTH = MONTH
    CE_YEAR = YEAR
    CE_DECADE = DECADE
    CE_CENTURY = CENTURY
    CE_MILLENNIUM = MILLENNIUM

    CE_SEASON = SEASON
    CE_SPRING = SPRING
    CE_FALL = FALL
    CE_WINTER = WINTER
    CE_SUMMER = SUMMER


class Season(Enum):
    SPRING = 0
    SUMMER = 1
    FALL = 2
    WINTER = 3


class Hemisphere(Enum):
    NORTH = 0
    SOUTH = 1


def get_active_hemisphere():
    """
    Get the hemisphere of the current location.

    Returns:
        Hemisphere (Enum): Hemisphere
    """
    from ovos_config import Configuration
    __latitude = Configuration().get("location", {}).get("coordinate", {})\
                .get("latitude", 38.971669)
    if __latitude < 0:
        return Hemisphere.SOUTH
    return Hemisphere.NORTH


def get_week_range(ref_date: datetime) -> Tuple[datetime, datetime]:
    """
    Get the start and end dates of the week containing the given reference date.

    Args:
        ref_date (datetime): The reference date to use for calculating the week
                             range.

    Returns:
        Tuple[datetime, datetime]: A tuple of datetime objects representing the
                                   start and end dates of the week containing the
                                   given reference date.
    """
    start = ref_date - timedelta(days=ref_date.weekday())
    end = start + timedelta(days=6)
    return start, end


def get_weekend_range(ref_date: datetime) -> Tuple[datetime, datetime]:
    """
    Args:
        ref_date (datetime): The reference date to use for calculating the weekend
                             range.

    Returns:
        Tuple[datetime, datetime]: Returns a tuple of datetime objects representing
                                   the start and end dates of the coming weekend.
    """
    if ref_date.weekday() < 5:
        start, _ = get_week_range(ref_date)
        start = start + timedelta(days=5)
    elif ref_date.weekday() == 5:
        start = ref_date
    elif ref_date.weekday() == 6:
        start = ref_date - timedelta(days=1)
    return start, start + timedelta(days=1)


def get_month_range(ref_date: datetime) -> Tuple[datetime, datetime]:
    """
    Get the start and end dates for the month containing the given reference date.

    Args:
        ref_date (datetime): The reference date to use for calculating the month
                             range.

    Returns:
        Tuple[datetime, datetime]: Returns a tuple of datetime objects representing
                                   the start and end dates.
    """
    start = ref_date.replace(day=1)
    if ref_date.month == 12:
        end = ref_date.replace(day=31)
    else:
        end = ref_date.replace(day=1, month=ref_date.month + 1) - timedelta(days=1)
    return start, end


def get_year_range(ref_date: datetime) -> Tuple[datetime, datetime]:
    """
    Get the start and end dates for the year containing the given reference date.

    Args:
        ref_date (datetime): The reference date to use for calculating the year
                                range.

    Returns:
        Tuple[datetime, datetime]: Returns a tuple of datetime objects representing
                                      the start and end dates.
    """

    start = ref_date.replace(day=1, month=1)
    end = ref_date.replace(day=31, month=12)
    return start, end


def get_decade_range(ref_date: datetime) -> Tuple[datetime, datetime]:
    """
    Get the start and end dates for the decade containing the given reference date.
    
    Args:
        ref_date (datetime): The reference date to use for calculating the decade
                             range.
                                
    Returns:
        Tuple[datetime, datetime]: Returns a tuple of datetime objects representing
                                   the start and end dates.
                                            
    """
    start = datetime(day=1, month=1, year=(ref_date.year // 10)*10)
    end = datetime(day=31, month=12, year=start.year + 9)
    return start, end


def get_century_range(ref_date: datetime) -> Tuple[datetime, datetime]:
    """
    Get the start and end dates for the century containing the given reference date.

    Args:
        ref_date (datetime): The reference date to use for calculating the century
                                range.
    
    Returns:
        Tuple[datetime, datetime]: Returns a tuple of datetime objects representing
                                        the start and end dates.
    """
    start = datetime(day=1, month=1, year=(ref_date.year // 100) * 100)
    end = datetime(day=31, month=12, year=start.year + 99)
    return start, end


def get_millennium_range(ref_date: datetime) -> Tuple[datetime, datetime]:
    """
    Get the start and end dates for the millennium containing the given reference date.

    Args:
        ref_date (datetime): The reference date to use for calculating the millennium
                                range.
    
    Returns:
        Tuple[datetime, datetime]: Returns a tuple of datetime objects representing
                                        the start and end dates.
    """
    start = datetime(day=1, month=1, year=(ref_date.year // 1000) * 1000)
    end = datetime(day=31, month=12, year=start.year + 999)
    return start, end


def get_date_ordinal(ordinal,
                     offset: Optional[int] = None,
                     ref_date: Optional[datetime] = None,
                     resolution: Enum = DateTimeResolution.DAY_OF_MONTH)\
                     -> datetime:
    """
    Returns a datetime object representing the date of the given ordinal 
    based on the resolution and offset.

    Example:
        >>> get_date_ordinal(1, ref_date=datetime(2020, 1, 1), resolution=DateTimeResolution.DAY_OF_MONTH)
        datetime.datetime(2020, 1, 1, 0, 0)
        >>> get_date_ordinal(2, ref_date=datetime(2020, 1, 1), resolution=DateTimeResolution.DAY_OF_WEEK)
        datetime.datetime(2019, 12, 31, 0, 0)

    Args:
        ordinal (int): The ordinal day of the month or week to get the date for.
        offset (int, optional): offset relative to the reference date.
        ref_date (datetime, optional): The reference date to use as a starting
                                       point. Defaults to None, which uses the
                                       current date.
        resolution (DateTimeResolution, optional): The resolution to use when
                                       calculating the date. Defaults to
                                       DateTimeResolution.DAY_OF_MONTH.

    Returns:
        datetime: A datetime object representing the date of the given ordinal
                  day of the month or week.
    """

    ordinal = int(ordinal)
    ref_date = ref_date or now_local()

    _decade = (ref_date.year // 10) * 10 or 1
    _century = (ref_date.year // 100) * 100 or 1
    _mil = (ref_date.year // 1000) * 1000 or 1

    # before present
    bp = datetime(year=1950, day=1, month=1)

    if resolution == DateTimeResolution.DAY:
        if ordinal < 0:
            raise OverflowError("The last day of existence can not be "
                                "represented")
        return datetime(year=1, day=1, month=1) + timedelta(days=ordinal - 1)

    elif resolution == DateTimeResolution.DAY_OF_REFERENCE:
        ref_date = ref_date.replace(hour=0, minute=0, second=0, microsecond=0)
        if ordinal < 0:
            raise ValueError("reference has no end date")
        return ref_date + relativedelta(days=ordinal - 1)

    elif resolution == DateTimeResolution.DAY_OF_WEEKEND:
        raise NotImplementedError

    # second day of last week, .. week 53
    elif resolution == DateTimeResolution.DAY_OF_WEEK:
        _start, _ = get_week_range(ref_date)
        if offset:
            _start += timedelta(days=offset*7)
        return _start + timedelta(days=ordinal-1)        

    # second friday of july, second day of july, last day of july
    elif resolution == DateTimeResolution.DAY_OF_MONTH:
        day = ordinal
        if ordinal == -1:
            # last day
            if ref_date.month + 1 == 13:
                return ref_date.replace(day=31, month=12)
            return ref_date.replace(month=ref_date.month + 1, day=1) - \
                timedelta(days=1)
        # {ordinal} {weekday}
        if offset:
            first_day = ref_date.replace(day=1).weekday()
            if offset >= first_day:
                day = 1 + offset - first_day + ((ordinal-1) * 7)
            else:
                day = 1 + offset - first_day + (ordinal * 7)
        return ref_date.replace(day=day)

    elif resolution == DateTimeResolution.DAY_OF_YEAR:
        day = ordinal
        if ordinal == -1:
            # last day
            return datetime(year=ref_date.year, day=31, month=12)
        # {ordinal} {weekday}
        if offset:
            first_day = ref_date.replace(day=1, month=1).weekday()
            if offset >= first_day:
                day = 1 + offset - first_day + ((ordinal-1) * 7)
            else:
                day = 1 + offset - first_day + (ordinal * 7)
        return datetime(year=ref_date.year, day=1, month=1) + \
                relativedelta(days=day-1)

    elif resolution == DateTimeResolution.DAY_OF_DECADE:
        if ordinal == -1:
            # last day
            if _decade + 10 == 10000:
                return datetime(year=9999, day=31, month=12)
            return datetime(year=_decade + 10, day=1, month=1) - timedelta(1)
        ordinal -= 1
        return datetime(year=_decade, day=1, month=1) + timedelta(days=ordinal)

    elif resolution == DateTimeResolution.DAY_OF_CENTURY:
        if ordinal == -1:
            # last day
            if _century + 100 == 10000:
                return datetime(year=9999, day=31, month=12)
            return datetime(year=_century + 100, day=1, month=1) - timedelta(1)

        return datetime(year=_century, day=1, month=1) + timedelta(days=ordinal - 1)

    elif resolution == DateTimeResolution.DAY_OF_MILLENNIUM:
        if ordinal == -1:
            # last day
            if _mil + 1000 == 10000:
                return datetime(year=9999, day=31, month=12)
            return datetime(year=_mil + 1000, day=1, month=1) - timedelta(1)
        return datetime(year=_mil, day=1, month=1) + timedelta(days=ordinal - 1)

    elif resolution == DateTimeResolution.WEEK:
        if ordinal < 0:
            raise OverflowError("The last week of existence can not be "
                                "represented")
        _day = datetime(1, 1, 1) + relativedelta(weeks=ordinal) - timedelta(days=1)
        _start, _end = get_week_range(_day)
        return _start

    elif resolution == DateTimeResolution.WEEK_OF_REFERENCE:
        ref_date = ref_date.replace(hour=0, minute=0, second=0, microsecond=0)
        if ordinal < 0:
            raise ValueError("reference has no end date")
        return ref_date + relativedelta(weeks=ordinal-1)

    elif resolution == DateTimeResolution.WEEK_OF_MONTH:
        if ordinal == -1:
            _day = ref_date.replace(day=1) + relativedelta(months=1) - \
                timedelta(days=1)
        else:
            if not 0 < ordinal <= 4:
                raise ValueError("months only have 4 weeks")

            _day = ref_date.replace(day=1) + relativedelta(weeks=ordinal) - \
                timedelta(days=1)

        _start, _end = get_week_range(_day)
        return _start

    elif resolution == DateTimeResolution.WEEK_OF_YEAR:
        if ordinal == -1:
            _day = ref_date.replace(day=31, month=12)
        else:
            _day = ref_date.replace(day=1, month=1) + relativedelta(
                weeks=ordinal) - timedelta(days=1)

        _start, _end = get_week_range(_day)
        return _start

    elif resolution == DateTimeResolution.WEEK_OF_DECADE:
        if ordinal == -1:
            _day = datetime(day=31, month=12, year=_decade + 9)
        else:
            _day = datetime(day=1, month=1, year=_decade) + \
                   relativedelta(weeks=ordinal) - timedelta(days=1)
        _start, _end = get_week_range(_day)
        return _start

    elif resolution == DateTimeResolution.WEEK_OF_CENTURY:
        if ordinal == -1:
            _day = datetime(day=31, month=12, year=_century + 99)
        else:
            _day = datetime(day=1, month=1, year=_century) + \
                   relativedelta(weeks=ordinal) - timedelta(days=1)

        _start, _end = get_week_range(_day)

        return _start
    elif resolution == DateTimeResolution.WEEK_OF_MILLENNIUM:
        if ordinal == -1:
            _day = datetime(day=31, month=12, year=_mil + 999)
        else:
            _day = datetime(day=1, month=1, year=_mil) + \
                   relativedelta(weeks=ordinal) - timedelta(days=1)

        _start, _end = get_week_range(_day)
        return _start

    elif resolution == DateTimeResolution.MONTH:
        if ordinal < 0:
            raise OverflowError("The last month of existence can not be "
                                "represented")
        return datetime(year=1, day=1, month=1) + relativedelta(months=ordinal - 1)

    elif resolution == DateTimeResolution.MONTH_OF_REFERENCE:
        ref_date = ref_date.replace(hour=0, minute=0, second=0, microsecond=0)
        if ordinal < 0:
            raise ValueError("reference has no end date")
        return ref_date + relativedelta(months=ordinal-1)

    elif resolution == DateTimeResolution.MONTH_OF_YEAR:
        if ordinal == -1:
            return ref_date.replace(month=12, day=1)
        return ref_date.replace(day=1, month=1) + \
            relativedelta(months=ordinal - 1)

    elif resolution == DateTimeResolution.MONTH_OF_CENTURY:
        if ordinal == -1:
            return datetime(year=_century + 99, day=1, month=12)
        _date = ref_date.replace(month=1, day=1, year=_century)
        _date += relativedelta(months=ordinal - 1)
        return _date

    elif resolution == DateTimeResolution.MONTH_OF_DECADE:
        if ordinal == -1:
            return datetime(year=_decade + 9, day=1, month=12)
        _date = ref_date.replace(month=1, day=1, year=_decade)
        _date += relativedelta(months=ordinal - 1)
        return _date

    elif resolution == DateTimeResolution.MONTH_OF_MILLENNIUM:
        if ordinal == -1:
            return datetime(year=_mil + 999, day=1, month=12)
        _date = ref_date.replace(month=1, day=1, year=_mil)
        _date += relativedelta(months=ordinal - 1)
        return _date

    elif resolution == DateTimeResolution.YEAR:
        if ordinal == -1:
            raise OverflowError("The last year of existence can not be "
                                "represented")
        if ordinal == 0:
            # NOTE: no year 0
            return datetime(year=1, day=1, month=1)
        return datetime(year=ordinal, day=1, month=1)
    
    elif resolution == DateTimeResolution.YEAR_OF_REFERENCE:
        ref_date = ref_date.replace(hour=0, minute=0, second=0, microsecond=0)
        if ordinal < 0:
            raise ValueError("reference has no end date")
        return ref_date + relativedelta(years=ordinal-1)

    elif resolution == DateTimeResolution.YEAR_OF_DECADE:
        if ordinal == -1:
            return datetime(year=_decade + 9, day=1, month=1)
        if ordinal == 0:
            # NOTE: no year 0
            return datetime(year=1, day=1, month=1)
        assert 0 < ordinal < 10
        return datetime(year=_decade + ordinal - 1, day=1, month=1)

    elif resolution == DateTimeResolution.YEAR_OF_CENTURY:
        if ordinal == -1:
            return datetime(year=_century + 99, day=1, month=1)
        if ordinal == 0:
            # NOTE: no year 0
            return datetime(year=1, day=1, month=1)
        return datetime(year=_century + ordinal - 1, day=1, month=1)

    elif resolution == DateTimeResolution.YEAR_OF_MILLENNIUM:
        if ordinal == -1:
            return datetime(year=_mil + 999, day=1, month=1)
        if ordinal == 0:
            # NOTE: no year 0
            return datetime(year=1, day=1, month=1)
        return datetime(year=_mil + ordinal - 1, day=1, month=1)

    elif resolution == DateTimeResolution.DECADE:
        if ordinal == -1:
            raise OverflowError("The last decade of existence can not be "
                                "represented")
        if ordinal == 1:
            return datetime(day=1, month=1, year=1)
        ordinal -= 1
        return datetime(year=ordinal * 10, day=1, month=1)

    elif resolution == DateTimeResolution.DECADE_OF_CENTURY:
        if ordinal == -1:
            return datetime(year=_century + 90, day=1, month=1)

        assert 0 < ordinal < 10

        if ordinal == 1:
            return datetime(day=1, month=1, year=_century)
        ordinal -= 1
        return datetime(year=_century + ordinal * 10, day=1, month=1)

    elif resolution == DateTimeResolution.DECADE_OF_MILLENNIUM:
        if ordinal == -1:
            return datetime(year=_mil + 990, day=1, month=1)

        assert 0 < ordinal < 1000

        if ordinal == 1:
            return datetime(day=1, month=1, year=_mil)
        ordinal -= 1
        return datetime(year=_mil + ordinal * 10,  day=1, month=1)
    
    elif resolution == DateTimeResolution.DECADE_OF_REFERENCE:
        ref_date = ref_date.replace(hour=0, minute=0, second=0, microsecond=0)
        if ordinal < 0:
            raise ValueError("reference has no end date")
        ordinal -= 1
        return ref_date + relativedelta(years=ordinal*10)

    elif resolution == DateTimeResolution.CENTURY:
        if ordinal == -1:
            raise OverflowError("The last century of existence can not be "
                                "represented")
        if ordinal == 1:
            return datetime(day=1, month=1, year=1)
        ordinal -= 1  # no century 0 / year 0
        return datetime(year=ordinal * 100, day=1, month=1)

    elif resolution == DateTimeResolution.CENTURY_OF_MILLENNIUM:
        if ordinal == -1:
            return datetime(year=_mil + 900, day=1, month=1)

        assert 0 < ordinal < 100

        if ordinal == 1:
            return datetime(day=1, month=1, year=_mil)
        ordinal -= 1
        return datetime(year=_mil + ordinal * 100,  day=1, month=1)
    
    elif resolution == DateTimeResolution.CENTURY_OF_REFERENCE:
        ref_date = ref_date.replace(hour=0, minute=0, second=0, microsecond=0)
        if ordinal < 0:
            raise ValueError("reference has no end date")
        ordinal -= 1
        return ref_date + relativedelta(years=ordinal*100)

    elif resolution == DateTimeResolution.MILLENNIUM:
        if ordinal < 0:
            raise OverflowError("The last millennium of existence can not be "
                                "represented")
        if ordinal == 1:
            return datetime(day=1, month=1, year=1)
        ordinal -= 1
        return datetime(year=ordinal * 1000, day=1, month=1)
    
    elif resolution == DateTimeResolution.MILLENNIUM_OF_REFERENCE:
        ref_date = ref_date.replace(hour=0, minute=0, second=0, microsecond=0)
        if ordinal < 0:
            raise ValueError("reference has no end date")
        ordinal -= 1
        return ref_date + relativedelta(years=ordinal*1000)

    elif resolution == DateTimeResolution.BEFORE_PRESENT_DAY:
        if ordinal < 0:
            raise OverflowError("Can not represent dates BC")
        return bp - relativedelta(days=ordinal)

    elif resolution == DateTimeResolution.BEFORE_PRESENT_WEEK:
        if ordinal < 0:
            raise OverflowError("Can not represent dates BC")
        _week = bp - relativedelta(weeks=ordinal)
        _start, _end = get_week_range(_week)
        return _end

    elif resolution == DateTimeResolution.BEFORE_PRESENT_MONTH:
        if ordinal < 0:
            raise OverflowError("Can not represent dates BC")
        return bp - relativedelta(months=ordinal)

    elif resolution == DateTimeResolution.BEFORE_PRESENT_YEAR:
        if ordinal < 0:
            raise OverflowError("Can not represent dates BC")
        return bp - relativedelta(years=ordinal)

    elif resolution == DateTimeResolution.BEFORE_PRESENT_DECADE:
        if ordinal < 0:
            raise OverflowError("Can not represent dates BC")
        return bp - relativedelta(years=10 * ordinal)

    elif resolution == DateTimeResolution.BEFORE_PRESENT_CENTURY:
        if ordinal < 0:
            raise OverflowError("Can not represent dates BC")
        return bp - relativedelta(years=100 * ordinal)

    elif resolution == DateTimeResolution.BEFORE_PRESENT_MILLENNIUM:
        if ordinal < 0:
            raise OverflowError("Can not represent dates BC")
        return bp - relativedelta(years=1000 * ordinal)

    elif resolution == DateTimeResolution.DAY_OF_SEASON:
        _start, _end = get_season_range(ref_date)
        if ordinal == -1:
            return _end
        return _start + relativedelta(days=ordinal - 1)

    elif resolution == DateTimeResolution.WEEK_OF_SEASON:
        _start, _end = get_season_range(ref_date)
        if ordinal == -1:
            return get_week_range(_end)[0]
        return get_week_range(_start + relativedelta(days=6))[0] + \
                relativedelta(weeks=ordinal - 1)

    elif resolution == DateTimeResolution.MONTH_OF_SEASON:
        _start, _end = get_season_range(ref_date)
        if ordinal == -1:
            return _end.replace(day=1)
        elif ordinal > 3:
            raise ValueError("Seasons only have 3 months")
        return next_resolution(_start, DateTimeResolution.MONTH) + \
                relativedelta(months=ordinal - 1)

    elif resolution == DateTimeResolution.JULIAN_DAY:
        if ordinal < 1721424.5:
            raise ValueError("Can not represent dates BC")
        _julian_day = ordinal
        dt = datetime.fromordinal(int(_julian_day) - 1721424)
        # hours
        dt += timedelta(days=_julian_day % 1)
        return dt
    
    elif resolution == DateTimeResolution.LILIAN_DAY:
        return datetime(1582, 10, 15) + timedelta(days=ordinal - 1)
    
    elif resolution == DateTimeResolution.UNIX_SECOND:
        return datetime.fromtimestamp(ordinal)
    
    elif resolution == DateTimeResolution.RATADIE_DAY:
        return datetime.fromordinal(ordinal)

    raise ValueError("Invalid DateTimeResolution")


def date_to_season(ref_date: Optional[datetime] = None,
                   hemisphere: Hemisphere = Hemisphere.NORTH,
                   metereological: bool = False):
    """
    Returns the season of the given date.

    Example:
        # astronomical
        >>> date_to_season(datetime(day=2, month=3, year=2024))
        Season.WINTER

        # metereological
        >>> date_to_season(datetime(day=2, month=3, year=2024),
                           metereological=True)
        Season.SPRING

    Args:
        ref_date, optional(datetime): The date to get the season of.
                                      Defaults to now.
        hemisphere: The hemisphere to use. Defaults to the northern hemisphere.
        metereological, optional(bool): Whether to use the metereological
                                        definition of the season. Defaults to
                                        astronomical.

    Returns:
        Enum: The season of the given date.    
    """
    ref_date = ref_date or now_local()
    if ref_date.year < 2020 or ref_date.year > 2043:
        metereological = True
    else:
        equinoxes = get_season_start_astro(ref_date.year, hemisphere)

    if hemisphere == Hemisphere.NORTH:
        fall = (
            datetime(day=1, month=9, year=ref_date.year, tzinfo=ref_date.tzinfo) \
                if metereological else equinoxes[Season.FALL].astimezone(ref_date.tzinfo),
            datetime(day=1, month=12, year=ref_date.year, tzinfo=ref_date.tzinfo) \
                if metereological else equinoxes[Season.WINTER].astimezone(ref_date.tzinfo)
        )
        spring = (
            datetime(day=1, month=3, year=ref_date.year, tzinfo=ref_date.tzinfo) \
                if metereological else equinoxes[Season.SPRING].astimezone(ref_date.tzinfo),
            datetime(day=1, month=6, year=ref_date.year, tzinfo=ref_date.tzinfo) \
                if metereological else equinoxes[Season.SUMMER].astimezone(ref_date.tzinfo)
        )
        summer = (
            datetime(day=1, month=6, year=ref_date.year, tzinfo=ref_date.tzinfo) \
                if metereological else equinoxes[Season.SUMMER].astimezone(ref_date.tzinfo),
            datetime(day=1, month=9, year=ref_date.year, tzinfo=ref_date.tzinfo) \
                if metereological else equinoxes[Season.FALL].astimezone(ref_date.tzinfo),
        )


        if fall[0].date() <= ref_date.date() < fall[1].date():
            return Season.FALL
        if summer[0].date() <= ref_date.date() < summer[1].date():
            return Season.SUMMER
        if spring[0].date() <= ref_date.date() < spring[1].date():
            return Season.SPRING
        return Season.WINTER

    else:
        spring = (
            datetime(day=1, month=9, year=ref_date.year, tzinfo=ref_date.tzinfo) \
                if metereological else equinoxes[Season.SPRING].astimezone(ref_date.tzinfo),
            datetime(day=1, month=12, year=ref_date.year, tzinfo=ref_date.tzinfo) \
                if metereological else equinoxes[Season.SUMMER].astimezone(ref_date.tzinfo)
        )
        fall = (
            datetime(day=1, month=3, year=ref_date.year, tzinfo=ref_date.tzinfo) \
                if metereological else equinoxes[Season.FALL].astimezone(ref_date.tzinfo),
            datetime(day=1, month=6, year=ref_date.year, tzinfo=ref_date.tzinfo) \
                if metereological else equinoxes[Season.WINTER].astimezone(ref_date.tzinfo)
        )
        winter = (
            datetime(day=1, month=6, year=ref_date.year, tzinfo=ref_date.tzinfo) \
                if metereological else equinoxes[Season.WINTER].astimezone(ref_date.tzinfo),
            datetime(day=1, month=9, year=ref_date.year, tzinfo=ref_date.tzinfo) \
                if metereological else equinoxes[Season.SPRING].astimezone(ref_date.tzinfo)
        )

        if fall[0].date() <= ref_date.date() < fall[1].date():
            return Season.FALL
        if winter[0].date() <= ref_date.date() < winter[1].date():
            return Season.WINTER
        if spring[0].date() <= ref_date.date() < spring[1].date():
            return Season.SPRING
        return Season.SUMMER


def season_to_date(season: Season,
                   year: Optional[int] = None,
                   tz: Optional[tzinfo] = None,
                   hemisphere: Hemisphere = Hemisphere.NORTH,
                   metereological: bool = False):
    """
    Returns the date of the given season.

    Example:
        >>> season_to_date(Season.SPRING, year=2018)
        datetime(day=1, month=3, year=2018)
    
    Args:
        season, Enum: The season to get the date of.
        year, optional(int): The year to get the date of. Defaults to the current
                             year.
        tz, optional(tzinfo): The timezone to use. Defaults to the local timezone.
        hemisphere, optional(Enum): The hemisphere to use. Defaults to the
                                    northern hemisphere.
        metereological, optional(bool): Whether to use the metereological
                                        definition of the season. Defaults to
                                        astronomical.
    
    Returns:
        datetime: The date of the given season.
    """
    if year is None:
        year = now_local().year
    elif not isinstance(year, int):
        year = year.year
    
    if tz is None:
        tz = now_local().tzinfo
    
    equinoxes = dict()
    # if year is out of range of provided equinoxes (2023 - 2043), force metereological date
    if year < 2020 or year > 2043:
        metereological = True
    else:
        equinoxes = get_season_start_astro(year, hemisphere)

    if hemisphere == Hemisphere.NORTH:
        if season == Season.SPRING:
            if metereological:
                return datetime(day=1, month=3, year=year, tzinfo=tz)
            else:
                return equinoxes[Season.SPRING].astimezone(tz)
        elif season == Season.FALL:
            if metereological:
                return datetime(day=1, month=9, year=year, tzinfo=tz)
            else:
                return equinoxes[Season.FALL].astimezone(tz)
        elif season == Season.WINTER:
            if metereological:
                return datetime(day=1, month=12, year=year, tzinfo=tz)
            else:
                return equinoxes[Season.WINTER].astimezone(tz)
        elif season == Season.SUMMER:
            if metereological:
                return datetime(day=1, month=6, year=year, tzinfo=tz)
            else:
                return equinoxes[Season.SUMMER].astimezone(tz)
    else:
        if season == Season.SPRING:
            if metereological:
                return datetime(day=1, month=9, year=year, tzinfo=tz)
            else:
                return equinoxes[Season.SPRING].astimezone(tz)
        elif season == Season.FALL:
            if metereological:
                return datetime(day=1, month=3, year=year, tzinfo=tz)
            else:
                return equinoxes[Season.FALL].astimezone(tz)
        elif season == Season.WINTER:
            if metereological:
                return datetime(day=1, month=6, year=year, tzinfo=tz)
            else:
                return equinoxes[Season.WINTER].astimezone(tz)
        elif season == Season.SUMMER:
            if metereological:
                return datetime(day=1, month=12, year=year, tzinfo=tz)
            else:
                return equinoxes[Season.SUMMER].astimezone(tz)
    raise ValueError("Unknown Season")


def next_season_date(season: Season, 
                     ref_date: Optional[datetime] = None,
                     hemisphere: Hemisphere = Hemisphere.NORTH,
                     metereological: bool = False):
    """
    Returns the date of the next season.
    
    Example:
        # astronomical
        >>> next_season_date(Season.SPRING,
                             ref_date=datetime(day=1, month=1, year=2024))
        datetime(2024, 3, 20, 3, 6, 24, tzinfo=<ref_date.tzinfo>)

        # metereological
        >>> next_season_date(Season.SPRING,
                             ref_date=datetime(day=1, month=1, year=2024),
                             metereological=True)
        datetime(2024, 3, 1, 0, 0, 0, tzinfo=<ref_date.tzinfo>)
    
    Args:
        season, Enum: The season to get the date of.
        ref_date, optional(datetime): The date to get the next season of.
                                      Defaults to now.
        hemisphere, optional(Enum): The hemisphere to use. Defaults to the
                                    northern hemisphere.
        metereological, optional(bool): Whether to use the metereological
                                        definition of the season. Defaults to
                                        astronomical.
    
    Returns:
        datetime: The date of the next season.
    """
    ref_date = ref_date or now_local()
    start_day = season_to_date(season,
                               ref_date.year,
                               ref_date.tzinfo,
                               hemisphere,
                               metereological)

    if ref_date.timetuple().tm_yday <= start_day.timetuple().tm_yday:
        # season is this year
        return start_day
    else:
        # season is next year
        return season_to_date(season,
                              ref_date.year + 1,
                              ref_date.tzinfo,
                              hemisphere,
                              metereological)


def last_season_date(season: Season,
                     ref_date: Optional[datetime] = None,
                     hemisphere: Hemisphere = Hemisphere.NORTH,
                     metereological: bool = False):
    """
    Returns the date of the last season.

    Example:
        # astronomical
        >>> last_season_date(Season.SPRING,
                             ref_date=datetime(day=1, month=1, year=2024))
        datetime(2023, 3, 20, 21, 24, 26, tzinfo=<ref_date.tzinfo>)

        # metereological
        >>> last_season_date(Season.SPRING,
                             ref_date=datetime(day=1, month=1, year=2024),
                             metereological=True)
        datetime(2023, 3, 1, 0, 0, 0, tzinfo=<ref_date.tzinfo>)
    
    Args:
        season, Enum: The season to get the date of.
        ref_date, optional(datetime): The date to get the last season of.
                                        Defaults to now.
        hemisphere, optional(Enum): The hemisphere to use. Defaults to the
                                    northern hemisphere.
        metereological, optional(bool): Whether to use the metereological
                                        definition of the season. Defaults to
                                        astronomical.
    
    Returns:
        datetime: The date of the last season.
    """
    ref_date = ref_date or now_local()

    _year = ref_date.year
    if ((ref_date.month < 3) or \
            (ref_date.month == 3 and ref_date.day < 20)):
        if season == Season.WINTER and \
                hemisphere == Hemisphere.NORTH:
            _year -= 1
        elif season == Season.SUMMER and \
                hemisphere == Hemisphere.SOUTH:
            _year -= 1

    start_day = season_to_date(season,
                               _year,
                               ref_date.tzinfo,
                               hemisphere,
                               metereological)
   
    if ref_date.timetuple().tm_yday <= start_day.timetuple().tm_yday:
        # season is previous year
        return season_to_date(season,
                              _year - 1,
                              ref_date.tzinfo,
                              hemisphere,
                              metereological)
    else:
        # season is this year
        return start_day


def get_season_range(ref_date: Optional[datetime] = None,
                     hemisphere: Hemisphere = Hemisphere.NORTH,
                     metereological: bool = False)\
    -> Tuple[datetime, datetime]:
    """
    Returns the date range of the current season.

    Example:
        # astronomical
        >>> get_season_range(ref_date=datetime(day=1, month=1, year=2024))
        (datetime(2023, 12, 22, 3, 27, 22, tzinfo=<ref_date.tzinfo>),
         datetime(2024, 3, 20, 3, 6, 24, tzinfo=<ref_date.tzinfo>))
        # metereological
        >>> get_season_range(ref_date=datetime(day=1, month=1, year=2024),
                             metereological=True)
        (datetime(2023, 12, 1, 0, 0, 0, tzinfo=<ref_date.tzinfo>),
         datetime(2024, 3, 1, 0, 0, 0, tzinfo=<ref_date.tzinfo>))

    Args:
        ref_date, optional(datetime): The date to get the season of.
                                      Defaults to now.
        hemisphere, optional(Enum): The hemisphere to use. Defaults to the
                                    northern hemisphere.
        metereological, optional(bool): Whether to use the metereological
                                        definition of the season. Defaults to
                                        astronomical.
    
    Returns:
        tuple(datetime, datetime): The start and end datetimes of the current
                                   season.
    """
    ref_date = ref_date or now_local()

    equinoxes = dict()
    # if year is out of range of provided equinoxes (2020 - 2043), force metereological date
    if ref_date.year < 2020 or ref_date.year > 2043:
        metereological = True
    else:
        equinoxes = get_season_start_astro(ref_date.year, hemisphere)

    if hemisphere == Hemisphere.NORTH:
        fall = (
            datetime(day=1, month=9, year=ref_date.year, tzinfo=ref_date.tzinfo) \
                if metereological else equinoxes[Season.FALL].astimezone(ref_date.tzinfo),
            datetime(day=1, month=12, year=ref_date.year, tzinfo=ref_date.tzinfo) \
                if metereological else equinoxes[Season.WINTER].astimezone(ref_date.tzinfo)
        )
        if ref_date > fall[1]:
            equinoxes_next = get_season_start_astro(ref_date.year + 1, hemisphere)
            winter = (
                datetime(day=1, month=12, year=ref_date.year, tzinfo=ref_date.tzinfo) \
                if metereological else equinoxes[Season.WINTER].astimezone(ref_date.tzinfo),
                datetime(day=1, month=3, year=ref_date.year + 1, tzinfo=ref_date.tzinfo) \
                if metereological else equinoxes_next[Season.SPRING].astimezone(ref_date.tzinfo)
            )
        else:
            equinoxes_last = get_season_start_astro(ref_date.year - 1, hemisphere)
            winter = (
                datetime(day=1, month=12, year=ref_date.year - 1, tzinfo=ref_date.tzinfo) \
                if metereological else equinoxes_last[Season.WINTER].astimezone(ref_date.tzinfo),
                datetime(day=1, month=3, year=ref_date.year, tzinfo=ref_date.tzinfo) \
                if metereological else equinoxes[Season.SPRING].astimezone(ref_date.tzinfo)
            )
        spring = (
            datetime(day=1, month=3, year=ref_date.year, tzinfo=ref_date.tzinfo) \
                if metereological else equinoxes[Season.SPRING].astimezone(ref_date.tzinfo),
            datetime(day=1, month=6, year=ref_date.year, tzinfo=ref_date.tzinfo) \
                if metereological else equinoxes[Season.SUMMER].astimezone(ref_date.tzinfo)
        )
        summer = (
            datetime(day=1, month=6, year=ref_date.year, tzinfo=ref_date.tzinfo) \
                if metereological else equinoxes[Season.SUMMER].astimezone(ref_date.tzinfo),
            datetime(day=1, month=9, year=ref_date.year, tzinfo=ref_date.tzinfo) \
                if metereological else equinoxes[Season.FALL].astimezone(ref_date.tzinfo)
        )

        if fall[0].date() <= ref_date.date() < fall[1].date():
            return fall
        if summer[0].date() <= ref_date.date() < summer[1].date():
            return summer
        if spring[0].date() <= ref_date.date() < spring[1].date():
            return spring
        if winter[0].date() <= ref_date.date() < winter[1].date():
            return winter

    else:
        spring = (
            datetime(day=1, month=9, year=ref_date.year, tzinfo=ref_date.tzinfo) \
                if metereological else equinoxes[Season.SPRING].astimezone(ref_date.tzinfo),
            datetime(day=1, month=12, year=ref_date.year, tzinfo=ref_date.tzinfo) \
                if metereological else equinoxes[Season.SUMMER].astimezone(ref_date.tzinfo)
        )
        fall = (
            datetime(day=1, month=3, year=ref_date.year, tzinfo=ref_date.tzinfo) \
                if metereological else equinoxes[Season.FALL].astimezone(ref_date.tzinfo),
            datetime(day=1, month=6, year=ref_date.year, tzinfo=ref_date.tzinfo) \
                if metereological else equinoxes[Season.WINTER].astimezone(ref_date.tzinfo)
        )
        if ref_date < fall[0]:
            equinoxes_last = get_season_start_astro(ref_date.year - 1, hemisphere)
            summer = (
                datetime(day=1, month=12, year=ref_date.year, tzinfo=ref_date.tzinfo) \
                if metereological else equinoxes_last[Season.SUMMER].astimezone(ref_date.tzinfo),
                datetime(day=1, month=3, year=ref_date.year, tzinfo=ref_date.tzinfo) \
                if metereological else equinoxes[Season.FALL].astimezone(ref_date.tzinfo)
            )
        else:
            equinoxes_next = get_season_start_astro(ref_date.year + 1, hemisphere)
            summer = (
                datetime(day=1, month=12, year=ref_date.year, tzinfo=ref_date.tzinfo) \
                if metereological else equinoxes[Season.SUMMER].astimezone(ref_date.tzinfo),
                datetime(day=1, month=3, year=ref_date.year, tzinfo=ref_date.tzinfo) \
                if metereological else equinoxes_next[Season.FALL].astimezone(ref_date.tzinfo)
            )
        winter = (
            datetime(day=1, month=6, year=ref_date.year, tzinfo=ref_date.tzinfo) \
                if metereological else equinoxes[Season.WINTER].astimezone(ref_date.tzinfo),
            datetime(day=1, month=9, year=ref_date.year, tzinfo=ref_date.tzinfo) \
                if metereological else equinoxes[Season.SPRING].astimezone(ref_date.tzinfo)
        )

        if fall[0].date() <= ref_date.date() < fall[1].date():
            return fall
        if winter[0].date() <= ref_date.date() < winter[1].date():
            return winter
        if spring[0].date() <= ref_date.date() < spring[1].date():
            return spring
        if summer[0].date() <= ref_date.date() < summer[1].date():
            return summer

    # If none of the conditions above are met, return an empty tuple
    return tuple()


def get_season_start_astro(year: int, hemisphere: Hemisphere = Hemisphere.NORTH) \
    -> Dict[Season, datetime]:
    """
    Returns the astronomical season starting datetimes for the given year.
    """

    _season_1 = Season.SPRING if hemisphere == Hemisphere.NORTH else Season.FALL
    _season_2 = Season.SUMMER if hemisphere == Hemisphere.NORTH else Season.WINTER
    _season_3 = Season.FALL if hemisphere == Hemisphere.NORTH else Season.SPRING
    _season_4 = Season.WINTER if hemisphere == Hemisphere.NORTH else Season.SUMMER
    
    equinoxes = {
                    2020:
                    {
                        _season_1: datetime(2020, 3, 20, 3, 49, 37, tzinfo=timezone.utc),
                        _season_2: datetime(2020, 6, 20, 21, 43, 41, tzinfo=timezone.utc),
                        _season_3: datetime(2020, 9, 22, 13, 30, 39, tzinfo=timezone.utc),
                        _season_4: datetime(2020, 12, 21, 10, 2, 20, tzinfo=timezone.utc)
                    },
                    2021:
                    {
                        _season_1: datetime(2021, 3, 20, 9, 37, 29, tzinfo=timezone.utc),
                        _season_2: datetime(2021, 6, 21, 3, 32, 10, tzinfo=timezone.utc),
                        _season_3: datetime(2021, 9, 22, 19, 21, 6, tzinfo=timezone.utc),
                        _season_4: datetime(2021, 12, 21, 15, 59, 18, tzinfo=timezone.utc)
                    },
                    2022:
                    {
                        _season_1: datetime(2022, 3, 20, 15, 33, 25, tzinfo=timezone.utc),
                        _season_2: datetime(2022, 6, 21, 9, 13, 51, tzinfo=timezone.utc),
                        _season_3: datetime(2022, 9, 23, 1, 3, 42, tzinfo=timezone.utc),
                        _season_4: datetime(2022, 12, 21, 21, 48, 13, tzinfo=timezone.utc)
                    },
                    2023: 
                    {
                        _season_1: datetime(2023, 3, 20, 21, 24, 26, tzinfo=timezone.utc),
                        _season_2: datetime(2023, 6, 21, 14, 57, 50, tzinfo=timezone.utc),
                        _season_3: datetime(2023, 9, 23, 6, 50, tzinfo=timezone.utc),
                        _season_4: datetime(2023, 12, 22, 3, 27, 22, tzinfo=timezone.utc)
                    },
                    2024: 
                    {
                        _season_1: datetime(2024, 3, 20, 3, 6, 24, tzinfo=timezone.utc),
                        _season_2: datetime(2024, 6, 20, 20, 51, tzinfo=timezone.utc),
                        _season_3: datetime(2024, 9, 22, 12, 43, 40, tzinfo=timezone.utc),
                        _season_4: datetime(2024, 12, 21, 9, 20, 34, tzinfo=timezone.utc)
                    },
                    2025: 
                    {
                        _season_1: datetime(2025, 3, 20, 9, 1, 29, tzinfo=timezone.utc),
                        _season_2: datetime(2025, 6, 21, 2, 42, 16, tzinfo=timezone.utc),
                        _season_3: datetime(2025, 9, 22, 18, 19, 20, tzinfo=timezone.utc),
                        _season_4: datetime(2025, 12, 21, 15, 3, 5, tzinfo=timezone.utc)
                    },
                    2026:
                    {
                        _season_1: datetime(2026, 3, 20, 14, 45, 57, tzinfo=timezone.utc),
                        _season_2: datetime(2026, 6, 21, 8, 24, 30, tzinfo=timezone.utc),
                        _season_3: datetime(2026, 9, 23, 0, 5, 13, tzinfo=timezone.utc),
                        _season_4: datetime(2026, 12, 21, 20, 50, 14, tzinfo=timezone.utc)
                    },
                    2027:
                    {
                        _season_1: datetime(2027, 3, 20, 20, 24, 41, tzinfo=timezone.utc),
                        _season_2: datetime(2027, 6, 21, 14, 10, 50, tzinfo=timezone.utc),
                        _season_3: datetime(2027, 9, 23, 6, 1, 43, tzinfo=timezone.utc),
                        _season_4: datetime(2027, 12, 22, 2, 42, 10, tzinfo=timezone.utc)
                    },
                    2028:
                    {
                        _season_1: datetime(2028, 3, 20, 2, 17, 8, tzinfo=timezone.utc),
                        _season_2: datetime(2028, 6, 20, 20, 2, tzinfo=timezone.utc),
                        _season_3: datetime(2028, 9, 22, 11, 45, 18, tzinfo=timezone.utc),
                        _season_4: datetime(2028, 12, 21, 8, 19, 40, tzinfo=timezone.utc)
                    },
                    2029:
                    {
                        _season_1: datetime(2029, 3, 20, 8, 1, 59, tzinfo=timezone.utc),
                        _season_2: datetime(2029, 6, 21, 1, 48, 18, tzinfo=timezone.utc),
                        _season_3: datetime(2029, 9, 22, 17, 38, 30, tzinfo=timezone.utc),
                        _season_4: datetime(2029, 12, 21, 14, 14, 6, tzinfo=timezone.utc)
                    },
                    2030:
                    {
                        _season_1: datetime(2030, 3, 20, 13, 52, 6, tzinfo=timezone.utc),
                        _season_2: datetime(2030, 6, 21, 7, 31, 19, tzinfo=timezone.utc),
                        _season_3: datetime(2030, 9, 22, 23, 26, 53, tzinfo=timezone.utc),
                        _season_4: datetime(2030, 12, 21, 20, 9, 38, tzinfo=timezone.utc)
                    },
                    2031:
                    {
                        _season_1: datetime(2031, 3, 20, 19, 40, 59, tzinfo=timezone.utc),
                        _season_2: datetime(2031, 6, 21, 13, 17, 8, tzinfo=timezone.utc),
                        _season_3: datetime(2031, 9, 23, 5, 15, 18, tzinfo=timezone.utc),
                        _season_4: datetime(2031, 12, 22, 1, 55, 34, tzinfo=timezone.utc)
                    },
                    2032:
                    {
                        _season_1: datetime(2032, 3, 20, 1, 21, 54, tzinfo=timezone.utc),
                        _season_2: datetime(2032, 6, 20, 19, 8, 46, tzinfo=timezone.utc),
                        _season_3: datetime(2032, 9, 22, 11, 10, 53, tzinfo=timezone.utc),
                        _season_4: datetime(2032, 12, 21, 7, 55, 57, tzinfo=timezone.utc)
                    },
                    2033:
                    {
                        _season_1: datetime(2033, 3, 20, 7, 22, 44, tzinfo=timezone.utc),
                        _season_2: datetime(2033, 6, 21, 1, 1, 9, tzinfo=timezone.utc),
                        _season_3: datetime(2033, 9, 22, 16, 51, 41, tzinfo=timezone.utc),
                        _season_4: datetime(2033, 12, 21, 13, 46, tzinfo=timezone.utc)
                    },
                    2034:
                    {
                        _season_1: datetime(2034, 3, 20, 13, 17, 30, tzinfo=timezone.utc),
                        _season_2: datetime(2034, 6, 21, 6, 44, 12, tzinfo=timezone.utc),
                        _season_3: datetime(2034, 9, 22, 22, 39, 35, tzinfo=timezone.utc),
                        _season_4: datetime(2034, 12, 21, 19, 34, 1, tzinfo=timezone.utc)
                    },
                    2035:
                    {
                        _season_1: datetime(2035, 3, 20, 19, 2, 45, tzinfo=timezone.utc),
                        _season_2: datetime(2035, 6, 21, 12, 33, 9, tzinfo=timezone.utc),
                        _season_3: datetime(2035, 9, 23, 4, 38, 57, tzinfo=timezone.utc),
                        _season_4: datetime(2035, 12, 22, 1, 30, 53, tzinfo=timezone.utc)
                    },
                    2036:
                    {
                        _season_1: datetime(2036, 3, 20, 1, 2, 51, tzinfo=timezone.utc),
                        _season_2: datetime(2036, 6, 20, 18, 32, 15, tzinfo=timezone.utc),
                        _season_3: datetime(2036, 9, 22, 10, 23, 20, tzinfo=timezone.utc),
                        _season_4: datetime(2036, 12, 21, 7, 12, 54, tzinfo=timezone.utc)
                    },
                    2037:
                    {
                        _season_1: datetime(2037, 3, 20, 6, 50, 17, tzinfo=timezone.utc),
                        _season_2: datetime(2037, 6, 21, 0, 22, 28, tzinfo=timezone.utc),
                        _season_3: datetime(2037, 9, 22, 16, 13, 7, tzinfo=timezone.utc),
                        _season_4: datetime(2037, 12, 21, 13, 7, 46, tzinfo=timezone.utc)
                    },
                    2038:
                    {
                        _season_1: datetime(2038, 3, 20, 12, 40, 39, tzinfo=timezone.utc),
                        _season_2: datetime(2038, 6, 21, 6, 9, 25, tzinfo=timezone.utc),
                        _season_3: datetime(2038, 9, 22, 22, 2, 18, tzinfo=timezone.utc),
                        _season_4: datetime(2038, 12, 21, 19, 2, 21, tzinfo=timezone.utc)
                    },
                    2039:
                    {
                        _season_1: datetime(2039, 3, 20, 18, 32, 4, tzinfo=timezone.utc),
                        _season_2: datetime(2039, 6, 21, 11, 57, 27, tzinfo=timezone.utc),
                        _season_3: datetime(2039, 9, 23, 3, 49, 39, tzinfo=timezone.utc),
                        _season_4: datetime(2039, 12, 22, 0, 40, 38, tzinfo=timezone.utc)
                    },
                    2040:
                    {
                        _season_1: datetime(2040, 3, 20, 0, 11, 44, tzinfo=timezone.utc),
                        _season_2: datetime(2040, 6, 20, 17, 46, 26, tzinfo=timezone.utc),
                        _season_3: datetime(2040, 9, 22, 9, 44, 57, tzinfo=timezone.utc),
                        _season_4: datetime(2040, 12, 21, 6, 32, 53, tzinfo=timezone.utc)
                    },
                    2041:
                    {
                        _season_1: datetime(2041, 3, 20, 6, 6, 51, tzinfo=timezone.utc),
                        _season_2: datetime(2041, 6, 20, 23, 35, 55, tzinfo=timezone.utc),
                        _season_3: datetime(2041, 9, 22, 15, 26, 36, tzinfo=timezone.utc),
                        _season_4: datetime(2041, 12, 21, 12, 18, 23, tzinfo=timezone.utc)
                    },
                    2042:
                    {
                        _season_1: datetime(2042, 3, 20, 11, 53, 22, tzinfo=timezone.utc),
                        _season_2: datetime(2042, 6, 21, 5, 15, 54, tzinfo=timezone.utc),
                        _season_3: datetime(2042, 9, 22, 21, 11, 37, tzinfo=timezone.utc),
                        _season_4: datetime(2042, 12, 21, 18, 4, 7, tzinfo=timezone.utc)
                    },
                    2043: 
                    {
                        _season_1: datetime(2043, 3, 20, 17, 27, 51, tzinfo=timezone.utc),
                        _season_2: datetime(2043, 6, 21, 10, 58, 26, tzinfo=timezone.utc),
                        _season_3: datetime(2043, 9, 23, 3, 7, tzinfo=timezone.utc),
                        _season_4: datetime(2043, 12, 22, 0, 1, 18, tzinfo=timezone.utc)
                    }
                }
    
    return equinoxes.get(year)


def next_resolution(ref_date: datetime, resolution: DateTimeResolution):
    """
    Returns the next date of the given resolution.

    Args:
        ref_date(datetime): The date to get the next date of.
        resolution(DateTimeResolution): The resolution of the next date to get.
    
    Returns:
        datetime: The next date of the given resolution.
    """
    # TODO: Season?
    if resolution == DateTimeResolution.MILLENNIUM:
        return datetime((ref_date.year // 1000 + 1) * 1000, 1, 1, tzinfo=ref_date.tzinfo).replace(hour=0, minute=0, second=0, microsecond=0)
    elif resolution == DateTimeResolution.CENTURY:
        return datetime((ref_date.year // 100 + 1) * 100, 1, 1, tzinfo=ref_date.tzinfo).replace(hour=0, minute=0, second=0, microsecond=0)
    elif resolution == DateTimeResolution.DECADE:
        return datetime((ref_date.year // 10 + 1) * 10, 1, 1, tzinfo=ref_date.tzinfo).replace(hour=0, minute=0, second=0, microsecond=0)
    elif resolution == DateTimeResolution.YEAR:
        return datetime(ref_date.year + 1, 1, 1, tzinfo=ref_date.tzinfo).replace(hour=0, minute=0, second=0, microsecond=0)
    elif resolution == DateTimeResolution.MONTH:
        _month = ref_date.month + 1
        _year = ref_date.year
        if ref_date.month == 12:
            _month = 1
            _year += 1
        return datetime(_year, _month, 1, tzinfo=ref_date.tzinfo).replace(hour=0, minute=0, second=0, microsecond=0)
    elif resolution == DateTimeResolution.WEEK:
        _ , end = get_week_range(ref_date)
        return (end + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    elif resolution == DateTimeResolution.DAY:
        return (ref_date + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    elif resolution == DateTimeResolution.HOUR:
        return (ref_date + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    elif resolution == DateTimeResolution.MINUTE:
        return (ref_date + timedelta(minutes=1)).replace(second=0, microsecond=0)
    elif resolution == DateTimeResolution.SECOND:
        return (ref_date + timedelta(seconds=1)).replace(microsecond=0)
    else:
        raise ValueError(f'Invalid resolution: {resolution}')


def get_week_number(ref_date=None):
    """
    Returns the week number of the year.

    Example:
        >>> get_week_number(ref_date=datetime(day=1, month=1, year=2018))
        1
    
    Args:
        ref_date, optional(datetime): The date to get the week number of.
                                      Defaults to now.
    
    Returns:
        int: The week number of the year.
    """
    ref_date = ref_date or now_local()
    return ref_date.isocalendar()[1]
