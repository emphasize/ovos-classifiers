import re
from enum import Enum
from datetime import datetime, timedelta, date
import math
from copy import deepcopy
from typing import List, Dict, Union, Any, Optional

from holidays import country_holidays
from dateutil import tz
from dateutil.relativedelta import relativedelta
from dateutil.easter import easter
from ovos_utils.time import DAYS_IN_1_MONTH, DAYS_IN_1_YEAR, now_local
from ovos_utils.json_helper import invert_dict

from ovos_classifiers.heuristics.numeric import EnglishNumberParser, GermanNumberParser
from .tokenize import ReplaceableNumber, ReplaceableTimedelta, ReplaceableDatetime, \
    ReplaceableTime, ReplaceableDate, Tokens, Token, word_tokenize
from ovos_classifiers.heuristics.time_helpers import DurationResolution, DateTimeResolution, \
    get_active_hemisphere, get_date_ordinal, get_year_range, get_month_range, Hemisphere, Season, \
    get_week_range, get_decade_range, get_century_range, get_millennium_range, get_season_range, \
    date_to_season, season_to_date, last_season_date, next_season_date, get_weekend_range, \
    next_resolution


# TODO: disentangle eras - calendar systems (not necessarily the same)
# If we go down the calendar system route, `kanon` might be a package to look at

_NAMED_ERAS = {
# NOTE: calendars have different year/month lengths and starting years,
# this is just a reference point in gregorian_date
# JULIAN/LUCIS has a AD date as we can't go BC

"AD": date(day=1, month=1, year=1),
"DIOCLETIAN": date(day=29, month=8, year=284),
"ARMENIAN": date(day=1, month=1, year=552),
"SCHAMSI": date(day=1, month=3, year=622),
"QAMARI": date(day=16, month=7, year=622),
"LUCIS": date(day=1, month=1, year=4001),
"THAI": date(day=6, month=4, year=1941),
"BAHAI": date(day=21, month=3, year=1844),
"PERSIAN": date(day=16, month=6, year=632),
"FRENCH": date(day=22, month=9, year=1792),
"POSITIVISTIC": date(day=1, month=1, year=1789),
"CHINESE-REP": date(day=1, month=1, year=1912),
"FASCIST": date(day=29, month=10, year=1922),
"DIANETIC": date(day=1, month=1, year=1950),
"ETHIOPIAN": date(day=27, month=8, year=8),
"UNIX": datetime(day=1, month=1, year=1970, tzinfo=tz.tzutc()),
"LILIAN": date(day=15, month=10, year=1582),
"JULIAN": date(day=1, month=1, year=4713),
"DARIAN": date(day=28, month=1, year=1611),
"RATADIE": date(day=1, month=1, year=1)

# TODO how to support year > 9999
# TODO how to support BC?
# "Vikrama Samvat,": date(day=1, month=1, year=-57)
# "Seleucid era": date(day=1, month=1, year=-312)
# "Anno Graecorum": date(day=1, month=1, year=-312)
# "Spanish era": date(day=1, month=1, year=-38)
# "era of Caesar": date(day=1, month=1, year=-38)
# "discordian era: date(day=1, month=1, year=-1166)
# "Hindu Calendar ": date(day=23, month=1, year=-3102)
# "Mayan era": date(day=11, month=8, year=-3113)
# "anno mundi": date(day=1, month=1, year=-3761),
# "Julian era": date(day=24, month=11, year=-4714),
# "Assyrian calendar": date(day=1, month=1, year=-4750),
# "Byzantine Calendar": date(day=1, month=1, year=-5509)
# "holocene era": date(day=1, month=1, year=-10000),
# "human era": date(day=1, month=1, year=-10000),
}


class EnglishTimeTagger:

    lang = "en-us"
    _STRING_WEEKDAY = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }
    _STRING_MONTH = {
        "jan": 1,
        "january": 1,
        "feb": 2,
        "february": 2,
        "mar": 3,
        "march": 3,
        "apr": 4,
        "april": 4,
        "may": 5,
        "jun": 6,
        "june": 6,
        "jul": 7,
        "july": 7,
        "aug": 8,
        "august": 8,
        "sep": 9,
        "september": 9,
        "oct": 10,
        "october": 10,
        "nov": 11,
        "november": 11,
        "dec": 12,
        "december": 12,
    }
    _SEASONS = {
        "spring": Season.SPRING,
        "summer": Season.SUMMER,
        "fall": Season.FALL,
        "autumn": Season.FALL,
        "winter": Season.WINTER
    }
    _HEMISPHERES = {
        Hemisphere.NORTH: ["north", "northern"],
        Hemisphere.SOUTH: ["south", "southern"]
    }

    # mapping dictionary for alternative names of named eras
    _ERAS_SYNONYMS = {
        "AD": ["after christ", "anno domini", "a.d.", "a. d.", "AD", "common era",
               "christian era", "christian calendar"],
        "UNIX": ["unix time", "unix seconds", "unix timestamp", "unix epoch"],
        "LUCIS": ["anno lucis"],
        "ARMENIAN": ["armenian calendar", "armenian era", "armenian epoch"],
        "THAI": ["thai calendar"],
        "LILIAN": ["lilian date", "lilian days", "lilian day", "L.D.", "L. D.", "LD",
                   "lilian epoch"],
        "DIANETIC": ["after dianetics"],
        "RATADIE": ["ratadie", "rata die", "r.d.", "r. d.", "RD"],
        "FASCIST": ["Era Fascista"],
        "PERSIAN": ["yazdegerd era", "Y.Z."],
        "BAHAI": ["bahai kalender", "bahai-kalender", "badi kalender", "badi-kalender", "bahai ära",
                  "bahai-ära", "badi ära", "badi-ära"],
        "JULIAN": ["julian date", "julian day", "julian days", "julian epoch", "JD", "J.D.", "J. D."],
        "FRENCH": ["french republican calender", "french revolutionary calender"],
        "DARIAN": ["Darian Mars year", "darian epoch", "darian era"],
        "POSITIVISTIC": ["positivist calendar", "positivist era", "positivistic era", "positivist epoch", "positivistic epoch"],
        "ETHIOPIAN" : ["incarnation era", "ethiopian calendar", "ethiopian epoch"],
        "CHINESE-REP": ["chinese republicanischen era", "Minguo era"],
        "SCHAMSI": ["hidschri schamsi", "sunhidschra"],
        "QAMARI": ["hidschri qamari", "moonhidschra"],
        "DIOCLETIAN": ["era of myrtyrs", "diocletian epoch", "diocletian epoch"]
    }

    # mapping dictionary for alternative names of named dates
    _NAMED_DATES = {
        "New Year's Day": ["New Year's Day", "New Years Day", "New Year's", "New Year"],
        "Epiphany": ["Three Kings' Day", "Twelfth Night", "Epiphany", "Twelfth Day", "Twelfthtide", "Little Christmas"],
        "Chinese New Year": ["Lunar New Year", "Spring Festival", "Yuan Tan", "Chinese New Year"],
        "Valentine's Day": ["Saint Valentine's Day", "Valentine's Day"],
        "World Women's Day": ["World Women's Day", "International Women's Day", "Women's Day", "Womens Day"],
        "St. Patrick's Day": ["Saint Patrick's Day", "St. Patrick's Day"],
        "Fat Tuesday": ["Mardi Gras", "Carnevale", "Carnival", "Shrove Tuesday", "Pancake Day", "Fat Tuesday"],
        "Ash Wednesday": ["Ash Wednesday", "Lent"],
        "Meteorological Spring": ["Meteorological Spring"],
        "Vernal Equinox": ["March Equinox", "March Equinox", "Vernal Equinox", "Spring Equinox"],
        "April Fool's Day": ["April Fools' Day", "April Fool's Day", "April Fools Day", "April Fool Day",
                             "All Fools' Day", "All Fools Day", "April Fools'", "April Fool's" , "April Fools"],
        "Easter Sunday": ["Resurrection Sunday", "Easter Sunday", "Easter"],
        "Good Friday": ["Holy Friday", "Good Friday"],
        "Easter Monday": ["Easter Monday"],
        "Palm Sunday": ["Palm Sunday", "Passion Sunday", "Hosanna Sunday", "Pascha Floridum", "Capitilavium"],
        "Maundy Thursday": ["Great and Holy Thursday", "Holy Thursday", "Green Thursday", "Covenant Thursday"],
        "Good Friday": ["Good Friday", "Holy Friday", "Great Friday"],
        "Holy Saturday": ["Holy Saturday", "Great Sabbath", "Black Saturday", "Easter Eve"],
        "Ascension Day": ["Ascension Day", "Ascension Thursday", "Holy Thursday"],
        "Pentecost": ["Whitsunday", "Pentecost", "Whitsun", "Whit Sun", "Whit Sunday"],
        "Whit Monday": ["Whit Monday", "Pentecost Monday", "Monday of the Holy Spirit"],
        "Corpus Christi": ["Corpus Christi", "Corpus Domini", "Body and Blood of Christ"],
        "Trinity Sunday": ["Holy Trinity Sunday", "Trinity Sunday"],
        "Labour Day": ["Labor Day", "Labour Day"],
        "Mother's Day": ["Mothering Sunday", "Mother's Day", "Mothers Day"],
        "Father's Day": ["Dad's Day", "Father's Day", "Fathers Day"],
        "Meteorological Summer": ["Meteorological Summer"],
        "Summer Solstice": ["Midsummer", "Summer Solstice"],
        "Canada Day": ["Canada's Birthday", "Canada Day", "Dominion Day", "National Day of Canada"],
        "American Independence Day": ["Independence Day"],
        "Bastille Day": ["French National Day", "Bastille Day", "National Day of France"],
        "International Friendship Day": ["Friendship Day", "International Friendship Day"],
        "Meteorological Autumn": ["Meteorological Autumn", "Meteorological Fall"],
        "Autumnal Equinox": ["Autumnal Equinox", "September Equinox", "September Equinox"],
        "German Unity Day": ["Day of German Unity", "German Unity Day", "German National Day", "National Day of Germany"],
        "Halloween": ["All Hallows' Eve", "Halloween"],
        "All Saints' Day": ["All Saints' Day", "All Saints Day"],
        "All Souls' Day": ["All Souls' Day", "All Souls Day", "Day of the Dead", "Dia de los Muertos"],
        "Remembrance Day": ["Veterans Day", "Remembrance Day"],
        "Thanksgiving Day": ["Turkey Day", "Thanksgiving Day", "Thanksgiving"],
        "Hanukkah": ["Chanukah", "Hanukkah"],
        "St. Nicholas Day": ["Saint Nicholas Day", "St. Nicholas Day", "St. Nick's Day", "St. Nicholas Eve",
                             "Feast of St. Nicholas", "Feast of Saint Nicholas"],
        "1st Advent": ["1 Advent Sunday", "1 Advent", "1 Sunday of Advent", "1 Sunday in Advent"],
        "2nd Advent": ["2 Advent Sunday", "2 Advent", "2 Sunday of Advent", "2 Sunday in Advent"],
        "3rd Advent": ["3 Advent Sunday", "3 Advent", "3 Sunday of Advent", "3 Sunday in Advent"],
        "4th Advent": ["4 Advent Sunday", "4 Advent", "4 Sunday of Advent", "4 Sunday in Advent"],
        "Meteorological Winter": ["Meteorological Winter"],
        "Winter Solstice": ["Winter Solstice", "Midwinter", "Yule", "Yuletide", "Yulefest"],
        "Christmas Eve": ["Christmas Eve"],
        "Christmas Day": ["Christmas Day", "Christmas"],
        "Boxing Day": ["St. Stephen's Day", "Boxing Day"],
        "Kwanzaa": ["Kwanza", "Kwanzaa"],
        "New Year's Eve": ["New Year's Eve"],
    }

    def extract_date(self, text: str,
                           ref_date: Optional[datetime] = None,
                           resolution: DateTimeResolution = DateTimeResolution.DAY,
                           hemisphere: Optional[Hemisphere] = None,
                           location_code: Optional[str] = None,
                           greedy: bool = False,

                           ) -> Optional[ReplaceableDate]:
        """
        Extracts date information from a sentence.  Parses many of the
        common ways that humans express dates and times, including relative dates
        like "5 days from today", "tomorrow', and "Tuesday".

        Args:
            text (str): the text to be interpreted
            anchorDate (:obj:`datetime`, optional): the date to be used for
                relative dating (for example, what does "tomorrow" mean?).
                Defaults to the current local date/time.
        Returns:
            extracted_date (datetime.date): 'date' is the extracted date as a datetime.date object.
                Returns 'None' if no date related text is found.

        Examples:

            >>> extract_datetime(
            ... "What is the weather like the day after tomorrow?",
            ... datetime(2017, 6, 30, 00, 00)
            ... )
            datetime.date(2017, 7, 2)

            >>> extract_datetime(
            ... "Set up an appointment 2 weeks from Sunday at 5 pm",
            ... datetime(2016, 2, 19, 00, 00)
            ... )
            datetime.date(2016, 3, 6)

            >>> extract_datetime(
            ... "Set up an appointment",
            ... datetime(2016, 2, 19, 00, 00)
            ... )
            None
        """
        replaceable_datetime = self.extract_datetime(text,
                                                     ref_date=ref_date,
                                                     resolution=resolution,
                                                     hemisphere=hemisphere,
                                                     location_code=location_code,
                                                     date_only=True,
                                                     greedy=greedy)
        if replaceable_datetime:
            date_tokens = [token for token in replaceable_datetime]  # if token.isDate or token.isDuration
            return ReplaceableDate(replaceable_datetime.value.date(), date_tokens)
        return None

    def extract_time(self, text: str,
                           ref_date: Optional[datetime] = None,
                           resolution: DateTimeResolution = DateTimeResolution.SECOND,
                           hemisphere: Optional[Hemisphere] = None,
                           location_code: Optional[str] = None,
                           ) -> Optional[ReplaceableTime]:
        """
        Extracts time information from a sentence.  Parses many of the
        common ways that humans express dates and times".

        Vague terminology are given arbitrary values, like:
            - morning = 8 AM
            - afternoon = 3 PM
            - evening = 7 PM

        If a time isn't supplied or implied, the function defaults to 12 AM

        Args:
            text (str): the text to be interpreted
            anchorDate (:obj:`datetime`, optional): the date to be used for
                relative dating (for example, what does "tomorrow" mean?).
                Defaults to the current local date/time.
        Returns:
            extracted_time (datetime.time): 'time' is the extracted time
                as a datetime.time object in the anchorDate (or default if None) timezone.
                Returns 'None' if no time related text is found.

        Examples:

            >>> extract_time(
            ... "What is the weather like the day after tomorrow?"
            ... )
            datetime.time(0, 0, 0)

            >>> extract_time(
            ... "Set up an appointment 2 weeks from Sunday at 5 pm"
            ... )
            datetime.time(17, 0, 0)

            >>> extract_datetime(
            ... "Set up an appointment"
            ... )
            None
        """
        replaceable_datetime = self.extract_datetime(text,
                                                     ref_date=ref_date,
                                                     resolution=resolution,
                                                     hemisphere=hemisphere,
                                                     location_code=location_code)
        if replaceable_datetime:
            time_tokens = [token for token in replaceable_datetime if token.isTime or token.isDuration]
            return ReplaceableTime(replaceable_datetime.value.time(), time_tokens)
        return None

    def extract_datetime(self, data: Union[str, Tokens],
                               ref_date: Optional[datetime] = None,
                               resolution: DateTimeResolution = DateTimeResolution.SECOND,
                               hemisphere: Optional[Hemisphere] = None,
                               location_code: Optional[str] = None,
                               date_only: bool = False,
                               greedy: bool = False):
        """

        :param date_str:
        :param ref_date:
        :param resolution:
        :param hemisphere:
        :param greedy: (bool) parse single number as years
        :return:
        """
        ref_date = ref_date or now_local()

        past_qualifiers = ["ago"]
        relative_qualifiers = ["from", "after", "since", "before"]
        relative_past_qualifiers = ["before"]
        of_qualifiers = ["of"]  # {Nth} day/week/month.... of month/year/century..
        set_qualifiers = ["is", "was"]  # "the year is 2021"

        more_markers = ["plus", "add", "+"]
        less_markers = ["minus", "subtract", "-"]
        past_markers = ["past", "last"]
        future_markers = ["next", "upcoming"]
        most_recent_qualifiers = ["last"]
        location_markers = ["in", "on", "at", "for"]

        daytimes = {"morning": (8,0),
                    "noon": (12,0),
                    "afternoon": (15,0),
                    "evening": (19,0),
                    "night": (22,0),
                    "tonight": (22,0),
                    "midnight": (0,0)}
        same_day_marker = ["today", "tonight"]
        pm_markers = ["PM", "pm", "p.m.", "P.M.", "afternoon", "evening", "night", "tonight"]
        daytime_night = ["night", "midnight", "tonight"]
        clock_markers = ["o'clock", "oclock", "AM", "PM", "am", "pm",
                        "p.m.", "a.m.", "P.M.", "A.M."]
        time_markers = ["at", "by", "around"]

        # TODO now is a datetime spec
        now = ["now"]
        near_dates = {"today": 0,
                      "tonight": 0,
                      "present": 0,
                      "tomorrow": 1,
                      "yesterday": -1}
        this = ["this", "current", "present", "the"]
        mid = ["mid", "middle"]
        day_literal = ["day", "days"]
        week_literal = ["week", "weeks"]
        weekend_literal = ["weekend", "weekends"]
        month_literal = ["month", "months"]
        year_literal = ["year", "years"]
        century_literal = ["century", "centuries"]
        decade_literal = ["decade", "decades"]
        millennium_literal = ["millennium", "millenia", "millenniums"]
        dateunit_literal = day_literal + week_literal + weekend_literal + \
            month_literal + year_literal + century_literal + decade_literal + \
            millennium_literal
        weekday_literal = list(self._STRING_WEEKDAY.keys())
        season_literal = ["season"]
        
        if isinstance(data, str):
            date_words = EnglishNumberParser().convert_words_to_numbers(data,
                                                                        ordinals=True)
        else:
            date_words = data

        self._tag_durations(date_words)

        extracted_date: Optional[datetime] = None
        delta: Union[timedelta, relativedelta] = timedelta(0)
        _delta: Optional[ReplaceableTimedelta] = None  # Timedelta Tokens
        date_found: bool = False
        
        time_found: bool = False
        _hour: Optional[int] = None
        _min: Optional[int] = None
        
        if hemisphere is None:
            hemisphere = self.extract_hemisphere(date_words) \
                         or get_active_hemisphere()

        # Preprocess named dates and named eras
        # named dates, "easter, christmas, .."
        named_dates: List[ReplaceableDate] = self.extract_named_dates(date_words, ref_date)
        named_date = named_dates[0] if named_dates else None
        if named_date:
            for tok in named_date:
                date_words.consume(tok)
                    
        # named_eras, ".. era of martyrs, a.d., ..."
        named_era = None
        for era, era_date in _NAMED_ERAS.items():
            for syn in self._ERAS_SYNONYMS[era]:
                if syn.lower() in date_words.lowercase:
                    regex = re.compile(r"\b%s[s]?(?:(?<=\.)|(?<=\b))" % (syn,), re.IGNORECASE)
                    match = regex.search(date_words.text)
                    if match:
                        named_era_tokens = date_words[match.span()]
                        for tok in named_era_tokens:
                            date_words.consume(tok)
                        if era == "UNIX":
                            resolution = DateTimeResolution.UNIX
                        elif era == "LILIAN":
                            resolution = DateTimeResolution.LILIAN
                        elif era == "JULIAN":
                            resolution = DateTimeResolution.JULIAN
                        elif era == "RATADIE":
                            resolution = DateTimeResolution.RATADIE
                        
                        named_era = ReplaceableDate(era_date, named_era_tokens)
                        break
    
        # is this a negative timespan?
        past_tok = date_words.find(past_qualifiers, allow_consumed=False)
        # is this relative to (after) a date?
        relative_tok = date_words.find(relative_qualifiers, allow_consumed=False)
        is_relative_past = relative_tok.word in relative_past_qualifiers \
            if relative_tok else False
        # is this a timespan in the future/past?
        math_tok = date_words.find(more_markers+less_markers, allow_consumed=False)
        is_sum = math_tok.word in more_markers if math_tok else False
        is_subtract = math_tok.word in less_markers if math_tok else False
        # cardinal of thing
        # 3rd day of the 4th month of 1994
        of_tok = date_words.find(of_qualifiers, allow_consumed=False)
                    
        # time parsing
        # we let this run even if date_only is True to tag the time
        # otherwise `greedy` would eventually interpret "6 30 pm" as year date
        is_pm = any(token.word in pm_markers for token in date_words)
        used_pm_marker = [token.word for token in date_words
                          if token.word in pm_markers]

        for token in date_words:

            if token.isConsumed or token.isSymbolic:
                continue
            _consumed: List[Token] = []

            # empty Token if oob
            tokPrevPrev = date_words[token.index - 2]
            tokPrev = date_words[token.index - 1]
            tokNext = date_words[token.index + 1]
            tokNextNext = date_words[token.index + 2]

            # TODO: 12:00:00
            if ":" in token.word or \
                    ("." in token.word and token.isNumeric and
                        tokNext.word in clock_markers):
                for components in [token.word.split(marker)
                                    for marker in (":", ".")]:
                    if len(components) == 2 and \
                            all(map(str.isdigit, components)) and\
                            int(components[0]) < 25 and int(components[1]) < 60:
                        _hstr, _mstr = components
                        _mstr = _mstr.ljust(2, "0")
                        _hour = int(_hstr)
                        _min = int(_mstr)
                        _consumed.append(token)
                # if tokNext.word in clock_markers:
                #     _consumed.append(tokNext)
            # parse {HH} o'clock, {HH} {MM} o'clock
            elif token.word in clock_markers:
                if not time_found:
                    if tokPrevPrev.isDigit and tokPrevPrev.number < 25 \
                            and tokPrev.isDigit and tokPrev.number < 60:
                        _hour = tokPrevPrev.number
                        _min = tokPrev.number
                        _consumed.extend([tokPrevPrev, tokPrev, token])
                    elif tokPrev.isDigit and tokPrev.number < 25:
                        _hour = tokPrev.number
                        _consumed.extend([tokPrev, token])
                else:
                    _consumed.append(token)
            # parse (at) {HH} {MM}, (at) {HH} (standalone)
            # TODO military time?
            elif token.word in time_markers and tokNext.isDigit:
                _hour = tokNext.number if tokNext.number < 24 else None
                _min = 0
                if _hour:
                    _consumed.append(tokNext)
                    if tokNextNext.isDigit and tokNextNext.number < 60:
                        _min = tokNextNext.number
                        _consumed.append(tokNextNext)
            # parse morning/afternoon/evening/night/noon/midnight
            elif token.word in daytimes:
                if not time_found:
                    _hour, _min = daytimes[token.word]
                _consumed.append(token)

            if _hour is not None and not date_only:
                # TODO Same day time check 7:30 at 12:00 -> 19:30
                _hour += 12 if is_pm and _hour < 12 and not \
                    (any(marker in used_pm_marker for marker in daytime_night)
                        and _hour < 6) else 0
                _min = 0 if _min is None else _min
                time_found = True
            else:
                _hour = _min = None
            
            for tok in _consumed:
                tok.isTime = True
                if not date_only:
                    tok.isConsumed = True

        # date parsing
        # parse {X} of {reference_date}
        if of_tok and not date_found:
            _idx = of_tok.index
            following_tok = date_words[_idx + 1:]
            # restrict to max. 3 tokens
            preceding_tok = date_words[_idx-4:_idx]  # 3rd day / 4th week of the year

            _resolutions = dict()
            _ref_day = None
            _anchor_date = None

            # Defaults
            _res = DateTimeResolution.DAY_OF_MONTH
            _unit = "day"

            _ordinal = preceding_tok.find_tag("isOrdinal")
            _number = _ordinal.number if _ordinal else None

            # parse "{ordinal} [{day/week/month/year/{weekday} ...}]"
            # {weekday} of -> {ordinal} day of
            if preceding_tok:
                #_token = preceding_tok.tokens[-2]
                
                _last = preceding_tok.find(most_recent_qualifiers)
                _unit_tok = preceding_tok.find(dateunit_literal + \
                                               weekday_literal)

                if _last:
                    _number = -1
                    date_words.consume(_last)
                if _unit_tok:
                    _unit = _unit_tok.lowercase
                    # tuesday -> 2nd day (only if not "2nd tuesday")
                    if _unit in weekday_literal and _number is None:
                        _number = self._STRING_WEEKDAY[_unit.rstrip("s")] + 1
                        _unit = "day"
                    if _number:
                        date_words.consume(_unit_tok)

            # # parse "{NUMBER}"
            # elif len(preceding_tok) == 1:
            #     _token = preceding_tok.tokens[0]
            #     if _token.isDigit:
            #         _number = _token.number
            #         date_words.consume(_token)
            
            # parse {reference_date}
            _replaceable_date = self.extract_datetime(following_tok,
                                                      ref_date,
                                                      resolution,
                                                      hemisphere,
                                                      greedy=True)

            # update consumed words
            if _replaceable_date:
                for tok in _replaceable_date:
                    date_words.consume(tok)
                _anchor_date = _replaceable_date.value

            # parse resolution {X} {day/week/month/year...} of {Y}
            if _number:
                # year is normally not spoken
                _request_year = False
                # parse "Nth {day/week/month/year...} of {YEAR}"
                if following_tok and date_words[of_tok.index+1].isDigit:
                    _request_year = True
                    _res = DateTimeResolution.DAY_OF_YEAR

                # parse "{NUMBER} day" or "{NUMBER} saturday"
                if _unit in day_literal or _unit in self._STRING_WEEKDAY.keys():
                    # "... of Y" (get the overall resolution)
                    _ref_day = self._STRING_WEEKDAY.get(_unit)
                    _resolutions = {
                        DateTimeResolution.DAY_OF_WEEK: week_literal,
                        DateTimeResolution.DAY_OF_MONTH: month_literal + \
                                                         list(self._STRING_MONTH.keys()),
                        DateTimeResolution.DAY_OF_YEAR: year_literal,
                        DateTimeResolution.DAY_OF_DECADE: decade_literal,
                        DateTimeResolution.DAY_OF_CENTURY: century_literal,
                        DateTimeResolution.DAY_OF_MILLENNIUM: millennium_literal
                        }
                    # default
                    if not _request_year:
                        _res = DateTimeResolution.DAY_OF_MONTH

                # parse "{NUMBER} week
                elif _unit in week_literal:
                    # "... of Y" (get the overall resolution)
                    _resolutions = {
                        DateTimeResolution.WEEK_OF_MONTH: month_literal + \
                                                          list(self._STRING_MONTH.keys()),
                        DateTimeResolution.WEEK_OF_YEAR: year_literal,
                        DateTimeResolution.WEEK_OF_DECADE: decade_literal,
                        DateTimeResolution.WEEK_OF_CENTURY: century_literal,
                        DateTimeResolution.WEEK_OF_MILLENNIUM: millennium_literal
                        }

                    if _request_year:
                        _res = DateTimeResolution.WEEK_OF_YEAR
                    else:
                        _res = DateTimeResolution.WEEK_OF_MONTH
                
                elif _unit in weekend_literal:
                    # "... of Y" (get the overall resolution)
                    _resolutions = {
                        DateTimeResolution.WEEKEND_OF_MONTH: month_literal + \
                                                             list(self._STRING_MONTH.keys()),
                        DateTimeResolution.WEEKEND_OF_YEAR: year_literal
                        }

                    if _request_year:
                        _res = DateTimeResolution.WEEKEND_OF_YEAR
                    else:
                        _res = DateTimeResolution.WEEKEND_OF_MONTH

                # parse "{NUMBER} month:
                elif _unit in month_literal:
                    # "... of Y" (get the overall resolution)
                    _resolutions = {
                        DateTimeResolution.MONTH_OF_YEAR: year_literal,
                        DateTimeResolution.MONTH_OF_DECADE: decade_literal,
                        DateTimeResolution.MONTH_OF_CENTURY: century_literal,
                        DateTimeResolution.MONTH_OF_MILLENNIUM: millennium_literal
                        }
                    # TODO DateTimeResolution.MONTH?
                    _res = DateTimeResolution.MONTH_OF_YEAR

                # parse "{NUMBER} year
                elif _unit in year_literal:
                    # "... of Y" (get the overall resolution)
                    _resolutions = {
                        DateTimeResolution.YEAR_OF_DECADE: decade_literal,
                        DateTimeResolution.YEAR_OF_CENTURY: century_literal,
                        DateTimeResolution.YEAR_OF_MILLENNIUM: millennium_literal
                        }

                    _res = DateTimeResolution.YEAR

                # parse "{NUMBER} decade
                elif _unit in decade_literal:
                    _resolutions = {
                        DateTimeResolution.DECADE_OF_CENTURY: century_literal,
                        DateTimeResolution.DECADE_OF_MILLENNIUM: millennium_literal
                        }

                    _res = DateTimeResolution.DECADE

                # parse "{NUMBER} century
                elif _unit in century_literal:
                    _resolutions = {
                        DateTimeResolution.CENTURY_OF_MILLENNIUM: millennium_literal
                        }

                    _res = DateTimeResolution.CENTURY

                # parse "{NUMBER} millennium
                elif _unit in millennium_literal:
                    _res = DateTimeResolution.MILLENNIUM

                # check _following_words to find the complete resolution
                # TODO: tie in month/.. names
                for _resolution, _res_words in _resolutions.items():
                    _res_tok = following_tok.find(_res_words)
                    if _res_tok:
                        _res = _resolution
                        break

            # Parse {Nth} day/week/month/year... of {reference_date}
            if _number and _anchor_date and _res:
                date_found = True
                extracted_date = get_date_ordinal(_number, _ref_day, _anchor_date, _res)
                date_words.consume(of_tok)

            # Parse {partial_date} of {partial_reference_date}
            # "summer of 1969"
            elif _anchor_date:
                # TODO should we allow invalid combinations?
                # "summer of january"
                # "12 may of october"
                # "1980 of 2002"

                _partial_date = self.extract_datetime(preceding_tok,
                                                      _anchor_date,
                                                      resolution,
                                                      hemisphere)

                if _partial_date:
                    date_found = True
                    extracted_date = _partial_date.value
                    date_words.consume(of_tok)

                    # update consumed words
                    for tok in _partial_date:
                        date_words.consume(tok)

        # parse {duration} ago
        # TODO past doesn't really need to exist, can be handled in relative past
        # always defaults to ref_date if no following date is found
        if past_tok and not date_found:
            # parse {duration} ago
            preceding_tok = date_words[:past_tok.index]
            deltas = self.extract_durations(preceding_tok,
                                            resolution=DurationResolution.RELATIVEDELTA_FALLBACK)
            if not deltas:
                raise RuntimeError(
                    "Could not extract duration from: " + preceding_tok.text)
            else:
                _delta = deltas[-1]
                date_words.consume([past_tok] + _delta.tokens)
                delta = _delta.value

        # parse {duration} after/from {date}
        # parse {duration} before {reference_date}
        if relative_tok and not date_found:
            # 1 hour 3 minutes from now
            # 5 days from now
            # 3 weeks after tomorrow
            # after tomorrow
            # 3 weeks before tomorrow
            # 5 days before today/tomorrow/tuesday
            
            preceding_tok = date_words[:relative_tok.index]
            following_tok = date_words[relative_tok.index + 1:]

            _anchor_date = None
            _resolution = None
            _offset = timedelta(0)

            if any(tok.isDuration for tok in preceding_tok):
                deltas  = self.extract_durations(preceding_tok,
                                                 resolution=DurationResolution.RELATIVEDELTA_FALLBACK)

                if deltas:
                    _delta = deltas[-1]
                    date_words.consume([relative_tok] + _delta.tokens)
                    _offset = _delta.value
                    if is_relative_past:
                        _offset *= -1
            
            # TODO: after {duration} missing
            # This points to a bigger problem: FIX ordinal -> int !!!!!
            # with this {ordinal} {unit} gets tagged as duration
                
            if any(tok.isDuration for tok in following_tok):
                _delta = self.extract_durations(following_tok,
                                                resolution=DurationResolution.RELATIVEDELTA_FALLBACK)[0]
                date_found = True
                extracted_date = ref_date
                _offset = _delta.value
                date_words.consume(_delta.tokens)
            else:
                _replaceable_date = self.extract_datetime(following_tok,
                                                        ref_date,
                                                        hemisphere=hemisphere,
                                                        date_only=True)
                if _replaceable_date is None and following_tok:
                    _year = following_tok.tokens[0]
                    if _year.isDigit and len(_year.word) == 4:
                        _anchor_date = datetime(day=1,
                                                month=1,
                                                year=_year.number,
                                                tzinfo=ref_date.tzinfo)
                        _resolution = DateTimeResolution.YEAR
                        date_words.consume(_year)
                elif _replaceable_date:
                    # update consumed words
                    for tok in _replaceable_date:
                        date_words.consume(tok)
                    _anchor_date = _replaceable_date.value
                
                _dateunit_tok = following_tok.find(dateunit_literal + \
                                                list(self._STRING_MONTH.keys()) + \
                                                list(self._STRING_WEEKDAY.keys()) + \
                                                list(near_dates.keys()))

                if _dateunit_tok:
                    _dateunit = _dateunit_tok.lowercase.rstrip('s')
                    if _dateunit not in dateunit_literal:
                        if _dateunit in self._STRING_MONTH and _anchor_date and \
                                not any(_anchor_date.day == t.number for t in following_tok):
                            _dateunit = "month"
                        else:
                            _dateunit = "day"
                    _resolution = DateTimeResolution[_dateunit.upper()]

                ref_date = _anchor_date or ref_date

                # after/before
                # .. day
                if _resolution == DateTimeResolution.DAY:
                    date_found = True
                    extracted_date = ref_date
                # .. week
                elif _resolution == DateTimeResolution.WEEK:
                    if not is_relative_past:
                        _, extracted_date = get_week_range(ref_date)
                    # NOTE: a request of {dateunit} (usually) comes back at the 
                    # beginning of that unit range 
                    else:
                        extracted_date = ref_date
                    date_found = True
                # .. month
                elif _resolution == DateTimeResolution.MONTH:
                    if not is_relative_past:
                        _, extracted_date = get_month_range(ref_date)
                    else:
                        extracted_date = ref_date
                    date_found = True
                # .. year
                elif _resolution == DateTimeResolution.YEAR:
                    if not is_relative_past:
                        _, extracted_date = get_year_range(ref_date)
                    else:
                        extracted_date = ref_date
                    date_found = True
                # .. decade
                elif _resolution == DateTimeResolution.DECADE:
                    if not is_relative_past:
                        _, extracted_date = get_decade_range(ref_date)
                    else:
                        extracted_date = ref_date
                    date_found = True
                # .. century
                elif _resolution == DateTimeResolution.CENTURY:
                    if not is_relative_past:
                        _, extracted_date = get_century_range(ref_date)
                    else:
                        extracted_date = ref_date
                    date_found = True
                # .. millennium
                elif _resolution == DateTimeResolution.MILLENNIUM:
                    if not is_relative_past:
                        _, extracted_date = get_millennium_range(ref_date)
                    else:
                        extracted_date = ref_date
                    date_found = True
                elif _anchor_date:
                    date_found = True
                    extracted_date = ref_date
                
                # correction for one day shift
                # gets applied if no duration was extracted before
                #                       (resolution)
                #                            |
                # ie "remind me after X" -> day after X
                # while "3 days after X" -> X + 3 days
                if is_relative_past:
                    _offset = _offset or timedelta(days=-1)
                elif not _offset:
                    extracted_date = next_resolution(extracted_date, resolution)
            
            extracted_date += _offset
            ref_date = _anchor_date or ref_date

        # parse {date} plus/minus {duration}
        if math_tok and not date_found:
            # parse {reference_date} plus {duration}
            # january 5 plus 2 weeks
            # parse {reference_date} minus {duration}
            # now minus 10 days
            following_tok = date_words[math_tok.index + 1:]
            deltas = self.extract_durations(following_tok,
                                            resolution=DurationResolution.RELATIVEDELTA_FALLBACK)

            if deltas:
                _delta = deltas[-1]
                date_words.consume([math_tok] + _delta.tokens)
                delta = _delta.value
            else:
                raise RuntimeError(
                    "Could not extract duration from: " + following_tok.text)
            preceding_tok = date_words[:math_tok.index]
            _replaceable_date = self.extract_datetime(preceding_tok,
                                                      ref_date,
                                                      date_only=date_only)
            
            if _replaceable_date is None and following_tok:
                _year = following_tok[0]
                if _year.isDigit and len(_year.word) == 4:
                    _anchor_date = datetime(day=1,
                                            month=1,
                                            year=_year.number,
                                            tzinfo=ref_date.tzinfo)
                    date_words.consume(_year)
            elif _replaceable_date:
                for t in _replaceable_date:
                    date_words.consume(t)
                    _anchor_date = _replaceable_date.value

            ref_date = _anchor_date or ref_date
            date_words.consume(math_tok)

        # relative timedelta found
        if delta and not date_found:
            try:
                if past_tok or is_subtract:
                    extracted_date = ref_date - delta
                else:
                    extracted_date = ref_date + delta

                date_found = True
            except OverflowError:
                # TODO how to handle BC dates
                # https://stackoverflow.com/questions/15857797/bc-dates-in-python
                if past_tok or is_subtract:
                    year_bc = delta.days // DAYS_IN_1_YEAR - ref_date.year
                    bc_str = str(year_bc) + " BC"
                    print("ERROR: extracted date is " + bc_str)
                else:
                    print("ERROR: extracted date is too far in the future")
                raise

        # iterate the word list to extract a date
        if not date_found:
            current_date = now_local()
            final_date = False

            if named_date:
                date_found = True
                ref_date = datetime.combine(named_date.value,
                                            datetime.min.time()).replace(tzinfo=ref_date.tzinfo)
            if named_era:
                date_found = True
                ref_date = datetime.combine(named_era.value,
                                            datetime.min.time()).replace(tzinfo=ref_date.tzinfo)
            
            # TODO: -> set to ref_date at the END
            extracted_date: Optional[datetime] = None

            for token in date_words:
                if final_date:
                    break  # no more date updates allowed

                if token.isConsumed or token.isSymbolic:
                    continue

                # empty Token if oob
                tokPrevPrev = date_words[token.index - 2]
                tokPrev = date_words[token.index - 1]
                tokNext = date_words[token.index + 1]
                tokNextNext = date_words[token.index + 2]
                tokNextNextNext = date_words[token.index + 3]

                # parse preformatted dates {YYYY/MM/DD}/{YYYY-MM-DD}
                # and derivatives {MM/DD/YYYY}/{DD.MM.YY}/{DD.MM.}
                # TODO: full iso8601 support (tokenized atm: ['2004-06-14T23', ':', '34:30']) 
                iso8601_date = list(
                    filter(lambda char: token.word.count(char) == 2, "./-"))
                if iso8601_date:
                    _date = token.word.split(iso8601_date[0])
                    # correction w/o year (11.12.)
                    if len(_date) == 3 and not _date[2]:
                        _date[2] = str(ref_date.year)
                    # correction 2 digit year (11.12.21) 
                    elif len(_date) == 3 and _date[2].isdigit() and len(_date[2]) == 2 \
                            and len(_date[0]) != 4:
                        _year = self._convert_year_abr(int(_date[2]))
                        date[2] = str(_year)
                    if len(_date) == 3 and all([(len(d) == 4 or (0 < len(d) <= 2))
                                            and d.isnumeric() for d in _date]):
                        if len(_date[0]) != 4:
                            _date.reverse()
                        _date = list(map(int, _date))
                        # disambiguate to the best of our ability
                        if "/" in token.word or _date[1] > 12:
                            _date[1], _date[2] = _date[2], _date[1]
                        try:
                            extracted_date = datetime(*_date)
                            date_found = True
                            date_words.consume(token)
                        except ValueError:
                            pass
                        else:
                            final_date = True

                # parse now (special case tied to current date)
                if token.word in now:
                    date_found = True
                    extracted_date = current_date
                    # final_date=True?
                    # token.isTime=True?
                    date_words.consume(token)
                # parse "today/yesterday/tomorrow"
                elif token.word in near_dates:
                    date_found = True
                    _offset = timedelta(days=near_dates[token.word])
                    extracted_date = (ref_date or current_date) + _offset
                    if not time_found:
                        extracted_date = extracted_date.replace(hour=0, minute=0, second=0)
                    date_words.consume(token)
                # parse {weekday}
                elif token.word in self._STRING_WEEKDAY:
                    date_found = True
                    extracted_date = extracted_date or ref_date
                    int_week = self._STRING_WEEKDAY[token.word]
                    _wd = ref_date.weekday()
                    _offset = 0
                    if tokPrev.word in past_markers:
                        # parse last {weekday}
                        if int_week <= _wd:
                            _offset = 7 - _wd + int_week
                        else:
                            _offset = 7 - int_week + _wd
                        extracted_date -= timedelta(days=_offset)
                        date_words.consume(tokPrev)
                    else:
                        # parse this {weekday}
                        # parse next {weekday}
                        if int_week < _wd:
                            _offset = 7 - _wd + int_week
                        else:
                            _offset = int_week - _wd
                        extracted_date += timedelta(days=_offset)

                        if tokPrev and (tokPrev.word in this or
                                        tokPrev.word in future_markers):
                            date_words.consume(tokPrev)

                    assert extracted_date.weekday() == int_week
                    date_words.consume(token)
                
                # # parse {month}
                # elif token.word in self._STRING_MONTH:
                #     date_found = True
                #     int_month = self._STRING_MONTH[token.word]

                #     extracted_date = ref_date.replace(month=int_month, day=1)

                #     if tokPrev.word in past_markers:
                #         if int_month > ref_date.month:
                #             extracted_date = extracted_date.replace(
                #                 year=ref_date.year - 1)
                #         date_words.consume(tokPrev)
                #     elif tokPrev.word in future_markers:
                #         if int_month < ref_date.month:
                #             extracted_date = extracted_date.replace(
                #                 year=ref_date.year + 1)
                #         date_words.consume(tokPrev)

                #     # parse {month} {DAY_OF_MONTH}
                #     if tokNext.isDigit and 0 < tokNext.number <= 31:
                #         extracted_date = extracted_date.replace(day=tokNext.number)
                #         date_words.consume(tokNext)
                #         # parse {month} {DAY_OF_MONTH} {YYYY}
                #         if resolution == DateTimeResolution.BEFORE_PRESENT and \
                #                 tokNextNext.isDigit:
                #             _year = get_date_ordinal(
                #                 tokNextNext.number, ref_date=extracted_date,
                #                 resolution=DateTimeResolution.BEFORE_PRESENT_YEAR).year
                #             extracted_date = extracted_date.replace(year=_year)
                #             date_words.consume(tokNextNext)
                #         elif len(tokNextNext.word) == 4 and \
                #                 tokNextNext.isDigit:
                #             _year = tokNextNext.number
                #             extracted_date = extracted_date.replace(year=_year)
                #             date_words.consume(tokNextNext)

                #     # parse {DAY_OF_MONTH} {month}
                #     elif tokPrev.isDigit and 0 < tokPrev.number <= 31:
                #         extracted_date = extracted_date.replace(day=tokPrev.number)
                #         date_words.consume(tokPrev)

                #     # parse {month} {YYYY}
                #     if tokNext.isDigit and len(tokNext.word) == 4:
                #         extracted_date = extracted_date.replace(year=tokNext.number)
                #         date_words.consume(tokNext)

                #     # parse {YYYY} {month}
                #     elif tokPrev.isDigit and len(tokPrev.word) == 4:
                #         extracted_date = extracted_date.replace(year=tokPrev.number)
                #         date_words.consume(tokPrev)

                #     date_words.consume(token)

                # parse {month}
                elif token.word in self._STRING_MONTH:
                    date_found = True
                    int_month = self._STRING_MONTH[token.word]
                    _year = None

                    _extracted_date = extracted_date or ref_date
                    _extracted_date = _extracted_date.replace(month=int_month, day=1)

                    if tokPrev.word in past_markers:
                        if int_month > ref_date.month:
                            _extracted_date = _extracted_date.replace(
                                year=_extracted_date.year - 1)
                        date_words.consume(tokPrev)
                    elif tokPrev.word in future_markers:
                        if int_month < ref_date.month:
                            _extracted_date = _extracted_date.replace(
                                year=_extracted_date.year + 1)
                        date_words.consume(tokPrev)

                    # parse {month} {DAY_OF_MONTH}
                    if (tokNext.isOrdinal or tokNext.isDigit) and 0 < tokNext.number <= 31:
                        _extracted_date = _extracted_date.replace(day=tokNext.number)
                        date_words.consume(tokNext)
                        # reset tokNext to parse potential year
                        tokNext = tokNextNext
                    # parse {DAY_OF_MONTH} {month}
                    elif (tokPrev.isDigit or tokPrev.isOrdinal) \
                            and 0 < tokPrev.number <= 31:
                        _extracted_date = _extracted_date.replace(day=tokPrev.number)
                        date_words.consume(tokPrev)
                    # parse {month} the {DAY_OF_MONTH}
                    elif tokNext.word == 'the' and tokNextNext.isOrdinal:
                        _extracted_date = _extracted_date.replace(day=tokNextNext.number)
                        date_words.consume(tokNextNext)
                        # reset tokNext to parse potential year
                        tokNext = tokNextNextNext
                    
                    # parse {month} {DAY_OF_MONTH} {YYYY}
                    if tokNext.isDigit and resolution == DateTimeResolution.BEFORE_PRESENT:
                        _year = get_date_ordinal(
                            tokNext.number, ref_date=ref_date,
                            resolution=DateTimeResolution.BEFORE_PRESENT_YEAR).year
                        _extracted_date = _extracted_date.replace(year=_year)
                        date_words.consume(tokNext)
                    # parse {month} {YYYY}
                    elif tokNext.isDigit and 1 < len(tokNext.word) <= 4:
                        if len(tokNext.word) >= 3:
                            _year = tokNext.number
                        else:
                            _year = self._convert_year_abr(tokNext.number, ref_date)
                        _extracted_date = _extracted_date.replace(year=_year)
                        date_words.consume(tokNext)
                    # parse {YYYY} {month}
                    elif tokPrev.isDigit and len(tokPrev.word) == 4:
                        _year = tokPrev.number
                        _extracted_date = _extracted_date.replace(year=_year)
                        date_words.consume(tokPrev)
                    
                    if extracted_date:
                        extracted_date = \
                            extracted_date.replace(month=_extracted_date.month,
                                                   day=_extracted_date.day)
                        if _year:
                            extracted_date = extracted_date.replace(year=_year)
                    else:
                        extracted_date = _extracted_date

                    date_words.consume(token)
                # parse "season"
                elif token.word in season_literal:
                    _start, _end = get_season_range(ref_date,
                                                    hemisphere=hemisphere)
                    # parse "in {Number} seasons"
                    if tokPrev.isDigit:
                        date_found = True
                        date_words.consume(tokPrev)
                        raise NotImplementedError
                    # parse "this season"
                    elif tokPrev.word in this:
                        date_found = True
                        extracted_date = _start
                        date_words.consume(tokPrev)
                    # parse "last season"
                    elif tokPrev.word in past_markers:
                        date_found = True
                        _end = _start - timedelta(days=2)
                        s = date_to_season(_end, hemisphere)
                        extracted_date = last_season_date(s, ref_date, hemisphere)
                        date_words.consume(tokPrev)
                    # parse "next season"
                    elif tokPrev.word in future_markers:
                        date_found = True
                        extracted_date = _end
                        date_words.consume(tokPrev)
                    # parse "mid season"
                    elif tokPrev.word in mid:
                        date_found = True
                        extracted_date = _start + (_end - _start) / 2
                        date_words.consume(tokPrev)

                    date_words.consume(token)                    
                # parse "spring/summer/autumn/fall/winter"
                elif token.word in self._SEASONS:
                
                    date_found = True
                    _season = self._SEASONS[token.word]
                    _year = ref_date.year
                    # year shift check
                    if ((ref_date.month < 3) or \
                            (ref_date.month == 3 and ref_date.day < 20)) and \
                            ref_date.year == now_local().year:
                        if _season == Season.WINTER and \
                                hemisphere == Hemisphere.NORTH:
                            _year = ref_date.year - 1
                        elif _season == Season.SUMMER and \
                                hemisphere == Hemisphere.SOUTH:
                            _year = ref_date.year - 1
                    
                    # parse spring {YYYY}/{YY}
                    if tokNext.isDigit and 1 < len(tokNext.word) <= 4:
                        if len(tokNext.word) == 2:
                            if tokNext.number <= 50:
                                _year = 2000 + tokNext.number
                            else:
                                _year = 1900 + tokNext.number
                        else:
                            _year = tokNext.number
                        extracted_date = season_to_date(_season,
                                                        _year,
                                                        ref_date.tzinfo,
                                                        hemisphere)
                        date_words.consume(tokNext)
                    # parse "in {Number} springs"
                    elif tokPrev.isDigit:
                        date_words.consume(tokPrev)
                        raise NotImplementedError
                    # parse "last spring"
                    elif tokPrev.word in past_markers:
                        extracted_date = last_season_date(_season,
                                                          ref_date,
                                                          hemisphere)
                        date_words.consume(tokPrev)
                    # parse "next spring"
                    elif tokPrev.word in future_markers:
                        extracted_date = next_season_date(_season,
                                                          ref_date,
                                                          hemisphere)
                        date_words.consume(tokPrev)

                    else:
                        # parse "[this] spring"
                        extracted_date = season_to_date(_season,
                                                        _year,
                                                        ref_date.tzinfo,
                                                        hemisphere)
                        if tokPrev.word in this:
                            date_words.consume(tokPrev)
                        # parse "mid {season}"
                        # TODO mid next season
                        elif tokPrev.word in mid:
                            _start, _end = get_season_range(extracted_date)
                            extracted_date = _start + (_end - _start) / 2
                            date_words.consume(tokPrev)

                    date_words.consume(token)
                # parse "day"
                elif token.word in day_literal:
                    # parse {ORDINAL} day
                    if tokPrev.isOrdinal:
                        date_found = True
                        if resolution == DateTimeResolution.BEFORE_PRESENT:
                            extracted_date = get_date_ordinal(
                                tokPrev.number, ref_date=ref_date,
                                resolution=DateTimeResolution.BEFORE_PRESENT_DAY)
                        else:
                            extracted_date = ref_date.replace(
                                day=tokPrev.number)
                        date_words.consume(tokPrev)
                    # parse day {NUMBER}
                    elif tokNext.isDigit:
                        date_found = True
                        extracted_date = ref_date.replace(day=tokNext.number)
                        date_words.consume(tokNext)
                    # parse "present day"
                    elif tokPrev.word in this:
                        date_found = True
                        extracted_date = ref_date
                        date_words.consume(tokPrev)
                    # parse "last day"
                    elif tokPrev.word in past_markers:
                        date_found = True
                        extracted_date = ref_date - timedelta(days=1)
                        date_words.consume(tokPrev)
                    # parse "next day"
                    elif tokPrev.word in future_markers:
                        date_found = True
                        extracted_date = ref_date + timedelta(days=1)
                        date_words.consume(tokPrev)

                    if extracted_date:
                        date_words.consume(token)
                        ref_date = extracted_date
                # parse "weekend"
                elif token.word in weekend_literal:
                    _is_weekend = ref_date.weekday() >= 5
                    # parse {ORDINAL} weekend
                    if tokPrev.isOrdinal:
                        date_found = True
                        date_words.consume(tokPrev)
                        if resolution == DateTimeResolution.BEFORE_PRESENT:
                            extracted_date = get_date_ordinal(
                                tokPrev.number,
                                resolution=DateTimeResolution.BEFORE_PRESENT_WEEKEND)
                        else:
                            extracted_date = get_date_ordinal(
                                tokPrev.number,
                                resolution=DateTimeResolution.WEEKEND_OF_MONTH)
                    # parse weekend {NUMBER}
                    elif tokNext.isDigit:
                        date_found = True
                        date_words.consume(tokNext)
                        raise NotImplementedError
                    # parse "this weekend"
                    elif tokPrev.word in this:
                        date_found = True
                        extracted_date, _end = get_weekend_range(ref_date)
                        date_words.consume(tokPrev)
                    # parse "next weekend"
                    elif tokPrev.word in future_markers:
                        date_found = True
                        if not _is_weekend:
                            extracted_date, _end = get_weekend_range(ref_date)
                        else:
                            extracted_date, _end = get_weekend_range(ref_date +
                                                                     timedelta(
                                                                     weeks=1))
                        date_words.consume(tokPrev)
                    # parse "last weekend"
                    elif tokPrev.word in past_markers:
                        date_found = True
                        extracted_date, _end = get_weekend_range(ref_date -
                                                                 timedelta(
                                                                 weeks=1))
                        date_words.consume(tokPrev)
                    date_words.consume(token)
                # parse "week"
                elif token.word in week_literal:
                    # parse {ORDINAL} week
                    if tokPrev.isOrdinal and 0 < tokPrev.number <= 53:
                        date_found = True
                        if resolution == DateTimeResolution.BEFORE_PRESENT:
                            _week = get_date_ordinal(
                                tokPrev.number,
                                resolution=DateTimeResolution.BEFORE_PRESENT_WEEK)
                        else:
                            _week = get_date_ordinal(
                                tokPrev.number,
                                ref_date=ref_date,
                                resolution=DateTimeResolution.WEEK_OF_YEAR)
                        extracted_date, _end = get_week_range(_week)
                        date_words.consume(tokPrev)
                    # parse "this week"
                    if tokPrev.word in this:
                        date_found = True
                        extracted_date, _end = get_week_range(ref_date)
                        date_words.consume(tokPrev)
                    # parse "last week"
                    elif tokPrev.word in past_markers:
                        date_found = True
                        _last_week = ref_date - timedelta(weeks=1)
                        extracted_date, _end = get_week_range(_last_week)
                        date_words.consume(tokPrev)
                    # parse "next week"
                    elif tokPrev.word in future_markers:
                        date_found = True
                        _last_week = ref_date + timedelta(weeks=1)
                        extracted_date, _end = get_week_range(_last_week)
                        date_words.consume(tokPrev)
                    # parse week {NUMBER}
                    elif tokNext.isDigit and 0 < tokNext.number <= 53:
                        date_found = True
                        extracted_date = get_date_ordinal(
                            tokNext.number,
                            ref_date=ref_date,
                            resolution=DateTimeResolution.WEEK_OF_YEAR)
                        date_words.consume(tokNext)
                    date_words.consume(token)
                # parse "month"
                elif token.word in month_literal:

                    # parse {ORDINAL} month
                    if tokPrev.isOrdinal and 0 < tokPrev.number <= 12:
                        date_found = True
                        if resolution == DateTimeResolution.BEFORE_PRESENT:
                            extracted_date = get_date_ordinal(
                                tokPrev.number,
                                resolution=DateTimeResolution.BEFORE_PRESENT_MONTH)
                        else:
                            extracted_date = get_date_ordinal(
                                tokPrev.number, ref_date=ref_date,
                                resolution=DateTimeResolution.MONTH_OF_YEAR)
                        date_words.consume(tokPrev)
                    # parse month {NUMBER}
                    elif tokNext.isDigit and 0 < tokNext.number <= 12:
                        date_found = True
                        extracted_date = get_date_ordinal(
                            tokNext.number, ref_date=ref_date,
                            resolution=DateTimeResolution.MONTH_OF_YEAR)
                        date_words.consume(tokNext)
                    # parse "this month"
                    elif tokPrev.word in this:
                        date_found = True
                        extracted_date = ref_date.replace(day=1)
                        date_words.consume(tokPrev)
                    # parse "next month"
                    elif tokPrev.word in future_markers:
                        date_found = True
                        _next_month = ref_date + timedelta(days=DAYS_IN_1_MONTH)
                        extracted_date = _next_month.replace(day=1)
                        date_words.consume(tokPrev)
                    # parse "last month"
                    elif tokPrev.word in past_markers:
                        date_found = True
                        _last_month = ref_date - timedelta(days=DAYS_IN_1_MONTH)
                        extracted_date = _last_month.replace(day=1)
                        date_words.consume(tokPrev)
                    date_words.consume(token)
                # parse "year"
                elif token.word in year_literal:
                    # parse "current year"
                    if tokPrev.word in this:
                        date_found = True
                        _extracted_date = get_date_ordinal(
                            ref_date.year,
                            resolution=DateTimeResolution.YEAR)
                        date_words.consume(tokPrev)
                    # parse "last year"
                    elif tokPrev.word in past_markers:
                        date_found = True
                        _extracted_date = get_date_ordinal(
                            ref_date.year - 1,
                            resolution=DateTimeResolution.YEAR)
                        date_words.consume(tokPrev)
                    # parse "next year"
                    elif tokPrev.word in future_markers:
                        date_found = True
                        _extracted_date = get_date_ordinal(
                            ref_date.year + 1,
                            resolution=DateTimeResolution.YEAR)
                        date_words.consume(tokPrev)
                    # parse Nth year
                    elif tokPrev.isOrdinal:
                        date_found = True
                        if resolution == DateTimeResolution.BEFORE_PRESENT:
                            _extracted_date = get_date_ordinal(
                                tokPrev.number,
                                resolution=DateTimeResolution.BEFORE_PRESENT_YEAR)
                        else:
                            _extracted_date = get_date_ordinal(
                                tokPrev.number - 1,
                                resolution=DateTimeResolution.YEAR)
                        date_words.consume(tokPrev)
                    elif tokNext.isDigit:
                        date_found = True
                        ref_date = ref_date.replace(year=tokNext.number)
                        # TODO: test behavious setting this to 1/1/YEAR
                        extracted_date = ref_date
                        date_words.consume(tokNext)

                    if extracted_date:
                        extracted_date = \
                            extracted_date.replace(year=_extracted_date.year)
                    else:
                        extracted_date = _extracted_date
                    date_words.consume(token)
                # parse "decade"
                elif token.word in decade_literal:
                    _decade = (ref_date.year // 10) + 1
                    # parse "current decade"
                    if tokPrev.word in this:
                        date_found = True
                        extracted_date = get_date_ordinal(
                            _decade,
                            resolution=DateTimeResolution.DECADE)
                        date_words.consume(tokPrev)
                    # parse "last decade"
                    elif tokPrev.word in past_markers:
                        date_found = True
                        extracted_date = get_date_ordinal(
                            _decade - 1,
                            resolution=DateTimeResolution.DECADE)
                        date_words.consume(tokPrev)
                    # parse "next decade"
                    elif tokPrev.word in future_markers:
                        date_found = True
                        extracted_date = get_date_ordinal(
                            _decade + 1,
                            resolution=DateTimeResolution.DECADE)
                        date_words.consume(tokPrev)
                    # parse Nth decade
                    elif tokPrev.isOrdinal:
                        date_found = True
                        if resolution == DateTimeResolution.BEFORE_PRESENT:
                            extracted_date = get_date_ordinal(
                                tokPrev.number,
                                resolution=DateTimeResolution.BEFORE_PRESENT_DECADE)
                        else:
                            extracted_date = get_date_ordinal(
                                tokPrev.number,
                                resolution=DateTimeResolution.DECADE)
                        date_words.consume(tokPrev)
                    date_words.consume(token)
                # parse "millennium"
                elif token.word in millennium_literal:
                    _mil = (ref_date.year // 1000) + 1
                    # parse "current millennium"
                    if tokPrev.word in this:
                        date_found = True
                        extracted_date = get_date_ordinal(
                            _mil, ref_date=ref_date,
                            resolution=DateTimeResolution.MILLENNIUM)
                        date_words.consume(tokPrev)
                    # parse "last millennium"
                    elif tokPrev.word in past_markers:
                        date_found = True
                        extracted_date = get_date_ordinal(
                            _mil - 1, ref_date=ref_date,
                            resolution=DateTimeResolution.MILLENNIUM)
                        date_words.consume(tokPrev)
                    # parse "next millennium"
                    elif tokPrev.word in future_markers:
                        date_found = True
                        extracted_date = get_date_ordinal(
                            _mil + 1, ref_date=ref_date,
                            resolution=DateTimeResolution.MILLENNIUM)
                        date_words.consume(tokPrev)
                    # parse Nth millennium
                    elif tokPrev.isOrdinal:
                        date_found = True
                        if resolution == DateTimeResolution.BEFORE_PRESENT:
                            extracted_date = get_date_ordinal(
                                tokPrev.number, ref_date=extracted_date,
                                resolution=DateTimeResolution.BEFORE_PRESENT_MILLENNIUM)
                        else:
                            extracted_date = get_date_ordinal(
                                tokPrev.number, ref_date=extracted_date,
                                resolution=DateTimeResolution.MILLENNIUM)
                        date_words.consume(tokPrev)
                    date_words.consume(token)
                # parse "century"
                elif token.word in century_literal:
                    _century = (ref_date.year // 100) + 1
                    # parse "current century"
                    if tokPrev.word in this:
                        date_found = True
                        extracted_date = get_date_ordinal(
                            _century, ref_date=ref_date,
                            resolution=DateTimeResolution.CENTURY)
                        date_words.consume(tokPrev)
                    # parse "last century"
                    elif tokPrev.word in past_markers:
                        date_found = True
                        extracted_date = get_date_ordinal(
                            _century - 1, ref_date=ref_date,
                            resolution=DateTimeResolution.CENTURY)
                        date_words.consume(tokPrev)
                    # parse "next century"
                    elif tokPrev.word in future_markers:
                        date_found = True
                        extracted_date = get_date_ordinal(
                            _century + 1, ref_date=ref_date,
                            resolution=DateTimeResolution.CENTURY)
                        date_words.consume(tokPrev)
                    # parse Nth century
                    elif tokPrev.isOrdinal:
                        date_found = True
                        if resolution == DateTimeResolution.BEFORE_PRESENT:
                            extracted_date = get_date_ordinal(
                                tokPrev.number, ref_date=extracted_date,
                                resolution=DateTimeResolution.BEFORE_PRESENT_CENTURY)
                        else:
                            extracted_date = get_date_ordinal(
                                tokPrev.number, ref_date=extracted_date,
                                resolution=DateTimeResolution.CENTURY)
                        date_words.consume(tokPrev)
                    date_words.consume(token)
                # parse day/mont/year is NUMBER
                elif token.word in set_qualifiers and tokNext.isDigit:
                    if tokPrev.word in dateunit_literal:
                        date_found = True
                        date_words.consume([tokPrev,token,tokNext])
                        if tokPrev.word in day_literal:
                            extracted_date = get_date_ordinal(
                                tokNext.number, ref_date=extracted_date,
                                resolution=DateTimeResolution.DAY_OF_MONTH)    
                        elif tokPrev.word in month_literal:
                            extracted_date = get_date_ordinal(
                                tokNext.number, ref_date=extracted_date,
                                resolution=DateTimeResolution.MONTH_OF_YEAR)
                        elif tokPrev.word in year_literal:
                            extracted_date = get_date_ordinal(
                                tokNext.number, ref_date=extracted_date,
                                resolution=DateTimeResolution.YEAR)
                        elif tokPrev.word in decade_literal:
                            extracted_date = get_date_ordinal(
                                tokNext.number, ref_date=extracted_date,
                                resolution=DateTimeResolution.DECADE)
                        elif tokPrev.word in century_literal:
                            extracted_date = get_date_ordinal(
                                tokNext.number, ref_date=extracted_date,
                                resolution=DateTimeResolution.CENTURY)
                        elif tokPrev.word in millennium_literal:
                            extracted_date = get_date_ordinal(
                                tokNext.number, ref_date=extracted_date,
                                resolution=DateTimeResolution.MILLENNIUM)
                        # TODO week of month vs week of year

                # bellow we parse standalone numbers, this is the major source
                # of ambiguity, caution advised

                # NOTE this is the place to check for requested
                # DateTimeResolution, usually not requested by the user but
                # rather used in recursion inside this very same method

                # NOTE2: the checks for XX_literal above may also need to
                # account for DateTimeResolution when parsing {Ordinal} {unit},
                # bellow refers only to default/absolute units

                # parse {YYYY} before present
                elif not date_found and token.isDigit and resolution == \
                        DateTimeResolution.BEFORE_PRESENT:
                    date_found = True
                    extracted_date = get_date_ordinal(
                        token.number, ref_date=extracted_date,
                        resolution=DateTimeResolution.BEFORE_PRESENT_YEAR)
                # parse {N} unix time
                elif not date_found and token.isDigit and resolution == \
                        DateTimeResolution.UNIX:
                    date_found = True
                    extracted_date = get_date_ordinal(
                        token.number, ref_date=extracted_date,
                        resolution=DateTimeResolution.UNIX_SECOND)
                # parse {N} julian days (since 1 January 4713 BC)
                elif not date_found and token.isDigit and resolution == \
                        DateTimeResolution.JULIAN:
                    date_found = True
                    extracted_date = get_date_ordinal(
                        token.number, ref_date=extracted_date,
                        resolution=DateTimeResolution.JULIAN_DAY)
                # TODO I'll take out the ratadie and CE resolutions for now, 
                # as the handling points to a bigger problem in the english handler,
                # namely the ordinal handling. 
                # Never really understood why an identifyable "type" is cast to int
                # just to not be able to differentiate between year and an ordinal
                # with Token(s) being nondestructible this should change
                # # parse {N} ratadie (days since 1/1/1)
                # elif not date_found and token.isDigit and resolution == \
                #         DateTimeResolution.RATADIE:
                #     date_found = True
                #     extracted_date = get_date_ordinal(
                #         token.number, ref_date=extracted_date,
                #         resolution=DateTimeResolution.RATADIE_DAY)
                # # parse {YYYY} common era (years since 1/1/1)
                # elif not date_found and token.isDigit and resolution == \
                #         DateTimeResolution.CE:
                #     date_found = True
                #     extracted_date = get_date_ordinal(
                #         token.number, ref_date=extracted_date,
                #         resolution=DateTimeResolution.CE_YEAR)
                # parse {N} lilian days
                elif not date_found and token.isDigit and resolution == \
                        DateTimeResolution.LILIAN:
                    date_found = True
                    extracted_date = get_date_ordinal(
                        token.number, ref_date=extracted_date,
                        resolution=DateTimeResolution.LILIAN_DAY)
                # parse {YYYYY} holocene year
                elif not date_found and token.isDigit and resolution == \
                        DateTimeResolution.HOLOCENE:
                    date_found = True
                    extracted_date = get_date_ordinal(
                        token.number, ref_date=extracted_date,
                        resolution=DateTimeResolution.HOLOCENE_YEAR)
                # parse {YYYYY} After the Development of Agriculture (ADA)
                elif not date_found and token.isDigit and resolution == \
                        DateTimeResolution.ADA:
                    date_found = True
                    extracted_date = get_date_ordinal(
                        token.number, ref_date=extracted_date,
                        resolution=DateTimeResolution.ADA_YEAR)
                # parse {YYYYY} "Creation Era of Constantinople"/"Era of the World"
                elif not date_found and token.isDigit and resolution == \
                        DateTimeResolution.CEC:
                    date_found = True
                    extracted_date = get_date_ordinal(
                        token.number, ref_date=extracted_date,
                        resolution=DateTimeResolution.CEC_YEAR)
                # parse {YYYY}
                # NOTE: assumes a full date has at least 3 digits
                elif greedy and token.isDigit and len(token.word) >= 3 \
                        and not token.isTime \
                        and not (tokPrev.word in dateunit_literal) \
                        and not (tokNext.word in dateunit_literal):
                    date_found = True
                    extracted_date = extracted_date or ref_date
                    extracted_date = extracted_date.replace(year=token.number)
                    date_words.consume(token)
                    greedy = False

                # parse {YY}
                elif greedy and token.isDigit \
                        and not token.isTime \
                        and not (tokPrev.word in dateunit_literal) \
                        and not (tokNext.word in dateunit_literal):
                    date_found = True
                    extracted_date = extracted_date or ref_date
                    _year = self._convert_year_abr(token.number, ref_date)

                    extracted_date = extracted_date.replace(year=_year)
                    date_words.consume(token)
                    greedy = False
                # parse {year} {era}
                # "1992 after christ"
                elif named_era and token.isDigit and tokNext in named_era:
                    date_found = True
                    ref_date = ref_date.replace(year=token.number)
                    extracted_date = ref_date
                    date_words.consume(token)
                # parse "the {YYYY/YY}s"
                elif not token.isDigit and token.word.rstrip("s").isdigit():
                    date_found = True
                    _year = token.word.rstrip("s")
                    if len(_year) == 2:
                        _year = self._convert_year_abr(int(_year), ref_date)
                    else:
                        _year = int(_year)
                    extracted_date = extracted_date or ref_date
                    extracted_date = extracted_date.replace(year=_year)
                    date_words.consume(token)


        if (date_found or (time_found and not date_only)):
            extracted_date = extracted_date or ref_date
            if not isinstance(extracted_date, datetime):
                    extracted_date = datetime.combine(extracted_date,
                                                      datetime.min.time())
            if not extracted_date.tzinfo:
                extracted_date = extracted_date.replace(tzinfo=ref_date.tzinfo)
            # TODO: this is going the easy route to tag date, should differentiate
            # in future iterations, furthermore (positional) markers shouldn't be tagged
            for token in date_words:
                if token.isConsumed and (not token.isDuration and not token.isTime):
                    token.isDate = True
            if time_found:
                extracted_date = extracted_date.replace(hour=_hour,
                                                        minute=_min,
                                                        second=0,
                                                        microsecond=0)
                if extracted_date.date() == now_local().date() and \
                        extracted_date.time() < now_local().time() and \
                        not date_words.find(same_day_marker):
                    extracted_date += timedelta(days=1)
            
            # apply global resolution
            # returns the start of the reference frame
            if resolution == DateTimeResolution.MINUTE:
                extracted_date = extracted_date.replace(second=0, microsecond=0)
            elif resolution == DateTimeResolution.HOUR:
                extracted_date = extracted_date.replace(minute=0, second=0, microsecond=0)
            elif resolution == DateTimeResolution.DAY:
                extracted_date = extracted_date.replace(hour=0, minute=0, second=0, microsecond=0)
            elif resolution == DateTimeResolution.WEEK:
                extracted_date, _ = get_week_range(extracted_date)
            elif resolution == DateTimeResolution.MONTH:
                extracted_date, _ = get_month_range(extracted_date)
            elif resolution == DateTimeResolution.YEAR:
                extracted_date, _ = get_year_range(extracted_date)
            elif resolution == DateTimeResolution.DECADE:
                extracted_date, _ = get_decade_range(extracted_date)
            elif resolution == DateTimeResolution.CENTURY:
                extracted_date, _ = get_century_range(extracted_date)
            elif resolution == DateTimeResolution.MILLENNIUM:
                extracted_date, _ = get_millennium_range(extracted_date)
            else:
                extracted_date = extracted_date.replace(microsecond=0)

            # backwards compatible: return the whole tokens list
            # to extract the remaining strings call property `remaining_text`
            # value = dt.value, remaining = dt.remaining_text
            dt = ReplaceableDatetime(extracted_date,
                                     date_words.tokens)
            return dt
        return None

    def extract_durations(self, data: Union[Tokens, str],
                                resolution=DurationResolution.TIMEDELTA) \
        -> List[ReplaceableTimedelta]:
        """
        Extract all timedeltas from a list of Tokens, with the words that
        represent them.

        Args:
            [Token]: The tokens to parse.

        Returns:
            [ReplaceableTimedelta]: A list of tuples, each containing a timedelta and a
                             string.

        """
        if isinstance(data, str):
            tokens = Tokens(data, lang="en-us")
        else:
            tokens = data

        # handle "a day" -> "1 day"
        for idx, tok in enumerate(tokens):
            if tok.word != "a" or idx == len(tokens) - 1:
                continue
            if tokens[idx + 1].word in {'microsecond', 'millisecond', 'second',
                                        'minute', 'hour', 'day', 'week', 'month',
                                        'year', 'decade', 'century', 'millennium'}:
                tokens.replace("1", [tok])

        numbers = EnglishNumberParser().extract_numbers(tokens, ordinals=True)

        durations = []
        for number in numbers:
            if number.end_index == tokens.end_index:
                break

            si_units: Dict[str, Any] = {
                'microseconds': 0,
                'milliseconds': 0,
                'seconds': 0,
                'minutes': 0,
                'hours': 0,
                'days': 0,
                'weeks': 0
                }

            next_token = tokens[number.end_index + 1]
            unit_en = next_token.word.rstrip("s")
            delta = None           

            if resolution == DurationResolution.TIMEDELTA:
                time_units = deepcopy(si_units)

                if unit_en + "s" in time_units:
                    time_units[unit_en+  "s"] += number.value
                elif unit_en == "month":
                    time_units["days"] += DAYS_IN_1_MONTH * number.value
                elif unit_en == "year":
                    time_units["days"] += DAYS_IN_1_YEAR * number.value
                elif unit_en == "decade":
                    time_units["days"] += 10 * DAYS_IN_1_YEAR * number.value
                elif unit_en == "century" or unit_en == "centurie":
                    time_units["days"] += 100 * DAYS_IN_1_YEAR * number.value
                elif unit_en == "millennium" or unit_en == "millennia":
                    time_units["days"] += 1000 * DAYS_IN_1_YEAR * number.value
                
                delta = timedelta(**time_units)
            
            elif resolution in [DurationResolution.RELATIVEDELTA,
                                DurationResolution.RELATIVEDELTA_APPROXIMATE,
                                DurationResolution.RELATIVEDELTA_FALLBACK,
                                DurationResolution.RELATIVEDELTA_STRICT]:
                
                time_units = deepcopy(si_units)
                time_units.pop('milliseconds')
                time_units.update({'months': 0,
                                   'years': 0})
                
                if unit_en + "s" in time_units:
                    time_units[unit_en+  "s"] += number.value
                elif unit_en == "decade":
                    time_units["years"] += 10 * number.value
                elif unit_en == "century" or unit_en == "centurie":
                    time_units["years"] += 100 * number.value
                elif unit_en == "millennium" or unit_en == "millennia":
                    time_units["years"] += 1000 * number.value
                
                 # microsecond, month, year must be ints
                time_units["microseconds"] = int(time_units["microseconds"])
                if resolution == DurationResolution.RELATIVEDELTA_FALLBACK:
                    for unit in ["months", "years"]:
                        value = time_units[unit]
                        _leftover, _ = math.modf(value)
                        if _leftover != 0:
                            print("[WARNING] relativedelta requires {unit} to be an "
                                "integer".format(unit=unit))
                            # fallback to timedelta resolution / raw tokens text with no flags
                            return self.extract_durations(tokens,
                                                          DurationResolution.TIMEDELTA)
                        time_units[unit] = int(value)
                elif resolution == DurationResolution.RELATIVEDELTA_APPROXIMATE:
                    _leftover, year = math.modf(time_units["years"])
                    time_units["months"] += 12 * _leftover
                    time_units["years"] = int(year)
                    _leftover, month = math.modf(time_units["months"])
                    time_units["days"] += DAYS_IN_1_MONTH * _leftover
                    time_units["months"] = int(month)
                else:
                    for unit in ["months", "years"]:
                        value = time_units[unit]
                        _leftover, _ = math.modf(value)
                        if _leftover != 0:
                            raise ValueError("relativedelta requires {unit} to be an "
                                             "integer".format(unit=unit))
                        time_units[unit] = int(value)
                
                delta = relativedelta(**time_units)
            
            else:
                # recalculate time in microseconds
                factors = {"microsecond": 1,
                           'millisecond': 1000,
                           'second': 1000*1000,
                           'minute': 1000*1000*60,
                           'hour': 1000*1000*60*60,
                           'day': 1000*1000*60*60*24,
                           'week': 1000*1000*60*60*24*7,
                           'month': 1000*1000*60*60*24*DAYS_IN_1_MONTH,
                           'year': 1000*1000*60*60*24*DAYS_IN_1_YEAR,
                           'decade': 1000*1000*60*60*24*DAYS_IN_1_YEAR*10,
                           'century': 1000*1000*60*60*24*DAYS_IN_1_YEAR*100,
                           'centurie': 1000*1000*60*60*24*DAYS_IN_1_YEAR*100,
                           'millennium': 1000*1000*60*60*24*DAYS_IN_1_YEAR*1000,
                           'millennia': 1000*1000*60*60*24*DAYS_IN_1_YEAR*1000
                        }
                if unit_en not in factors:
                    continue
                
                microseconds = factors[unit_en] * number.value

                if resolution == DurationResolution.TOTAL_MICROSECONDS:
                    delta = microseconds
                elif resolution == DurationResolution.TOTAL_MILLISECONDS:
                    delta = microseconds / factors['millisecond']
                elif resolution == DurationResolution.TOTAL_SECONDS:
                    delta = microseconds / factors['second']
                elif resolution == DurationResolution.TOTAL_MINUTES:
                    delta = microseconds / factors['minute']
                elif resolution == DurationResolution.TOTAL_HOURS:
                    delta = microseconds / factors['hour']
                elif resolution == DurationResolution.TOTAL_DAYS:
                    delta = microseconds / factors['day']
                elif resolution == DurationResolution.TOTAL_WEEKS:
                    delta = microseconds / factors['week']
                elif resolution == DurationResolution.TOTAL_MONTHS:
                    delta = microseconds / factors['month']
                elif resolution == DurationResolution.TOTAL_YEARS:
                    delta = microseconds / factors['year']
                elif resolution == DurationResolution.TOTAL_DECADES:
                    delta = microseconds / factors['decade']
                elif resolution == DurationResolution.TOTAL_CENTURIES:
                    delta = microseconds / factors['century']
                elif resolution == DurationResolution.TOTAL_MILLENNIUMS:
                    delta = microseconds / factors['millennium']
                else:
                    raise ValueError

            # if we have any duration, save the extraction, else it was just a number
            if delta:
                toks = tokens[number.start_index:number.end_index+2]
                # mark token as duration
                for tok in toks:
                    tok.isDuration = True

                # if we have a previous duration without intermediate tokens, a comma or 
                # connected with "and", merge
                prev_dur = None
                prev_tok = None if number.start_index == 0 else tokens[number.start_index - 1]
                if len(durations):
                    prev_dur = durations[-1]

                if prev_dur and \
                        any((prev_dur.end_index == number.start_index - 1,
                             prev_dur.end_index == number.start_index - 2 and 
                             (prev_tok.word == "and" or prev_tok.isComma)
                            )):
                    delta = prev_dur.value + delta
                    toks  = tokens[prev_dur.start_index:number.end_index+2]
                    if isinstance(delta, (float, int)):
                        durations[-1] = ReplaceableNumber(delta, toks)
                    else:
                        durations[-1] = ReplaceableTimedelta(delta, toks)
                else:
                    durations.append(ReplaceableTimedelta(delta, toks)
                                     if not isinstance(delta, (float, int))
                                     else ReplaceableNumber(delta, toks))

        durations.sort(key=lambda n: n.start_index)
        return durations

    def _tag_durations(self, tokens: Tokens):
        """
        Tags durations in the tokens.
        """
        self.extract_durations(tokens)
     
    def extract_duration(self, data: Union[Tokens, str],
                         resolution=DurationResolution.TIMEDELTA) \
        -> Optional[ReplaceableTimedelta]:
        durations = self.extract_durations(data, resolution=resolution)
        if len(durations) == 0:
            return None
        return durations[0]
    
    def extract_hemisphere(self, data: Union[Tokens, str],
                                 markers: Optional[List[str]] = None,
                                 ner: Optional[callable] = None) \
        -> Optional[Hemisphere]:
        """
        Extracts the hemisphere from the text.
        """

        # TODO Best to return a Location object with the hemisphere

        if ner is None:
            try:
                from simple_NER.annotators.locations import LocationNER

                ner = LocationNER()
            except ImportError:
                ner = None
                print("Location extraction disabled")
                print("Run pip install simple_NER>=0.4.1")

        markers = markers or ["in", "on", "at", "for"]
        hemisphere_literal = ["hemisphere", "hemispheres"]
        hemisphere = None

        if isinstance(data, str):
            tokens = Tokens(data, self.lang)
        else:
            tokens = data

        # parse {date} at {location}
        for token in tokens:
            if token.word in markers:
                # this is used to parse seasons, which depend on
                # geographical location
                # "i know what you did last summer",  "winter is coming"
                # usually the default will be set automatically based on user
                # location

                # NOTE these words are kept in the utterance remainder
                # they are helpers but not part of the date itself

                # parse {date} at north hemisphere
                if tokens[token.index+1].word in self._HEMISPHERES[Hemisphere.NORTH] \
                        and tokens[token.index+2].word in hemisphere_literal:
                    hemisphere = Hemisphere.NORTH
                # parse {date} at south hemisphere
                elif tokens[token.index+1].word in self._HEMISPHERES[Hemisphere.SOUTH] \
                        and tokens[token.index+2].word in hemisphere_literal:
                    hemisphere = Hemisphere.SOUTH
                # parse {date} at {country/city}
                elif ner is not None:
                    # parse string for Country names
                    for r in ner.extract_entities(tokens[token.index+1].word):
                        if r.entity_type == "Country":
                            if r.data["latitude"] < 0:
                                hemisphere = Hemisphere.SOUTH
                            else:
                                hemisphere = Hemisphere.NORTH
                    else:
                        #  or Capital city names
                        for r in ner.extract_entities(tokens[token.index+1].word):
                            if r.entity_type == "Capital City":
                                if r.data["hemisphere"].startswith("s"):
                                    hemisphere = Hemisphere.SOUTH
                                else:
                                    hemisphere = Hemisphere.NORTH

        return hemisphere

    def extract_named_dates(self, data: Union[str, Tokens],
                                  ref_date: Optional[datetime] = None) \
        -> List[ReplaceableDate]:
        """
        Returns a alist of named dates if found in the text.
        """
        ref_date = ref_date or now_local()
        extracted_named_dates = []
        named_tokens = []

        if isinstance(data, str):
            tokens = Tokens(data, self.lang)
        else:
            tokens = data

        # NOTE: the tricky thing here is
        # * variable dates like easter,.. (ie. you cant do easter - 1 year)
        # * easter last year/.. years ago (fixed), last easter (dependent on when you ask)
        
        upcoming = ["next", "upcoming"]
        last = ["last", "previous", "past"]
        this = ["this", "current"]
                
        # parse the year from the utterance
        year_token = tokens.find(["year", "years"])
        _year = None
        if year_token:
            tokNext = tokens[year_token.index + 1]
            tokPrev = tokens[year_token.index - 1]
            tokPrevPrev = tokens[year_token.index - 2]
            # easter in/before 2 years
            if year_token.isDuration and tokPrev.isDigit \
                    and tokPrevPrev.lowercase in ["before", "in"]:
                if tokPrevPrev.lowercase == "before":
                    _year = ref_date.year - tokPrev.number
                    named_tokens.extend([year_token, tokPrev, tokPrevPrev])
                elif tokPrevPrev.lowercase == "in":
                    _year = ref_date.year + tokPrev.number
                    named_tokens.extend([year_token, tokPrev, tokPrevPrev])
            # .. 2 years ago
            elif year_token.isDuration and tokPrev.isDigit \
                    and tokNext.lowercase in ["before", "ago"]:
                    _year = ref_date.year - tokPrev.number
                    named_tokens.extend([year_token, tokPrev, tokNext])
            # .. year 2024
            elif tokNext.isDigit:
                if tokNext.number < 100:
                    _year = ((ref_date.year // 100) * 100) + tokNext.number
                else:
                    _year = tokNext.number
                named_tokens.extend([year_token, tokNext])
            # .. last year
            elif tokPrev.lowercase in last:
                _year = ref_date.year - 1
                named_tokens.extend([year_token, tokPrev])
            # .. next year
            elif tokPrev.lowercase in upcoming:
                _year = ref_date.year + 1
                named_tokens.extend([year_token, tokPrev])
            # .. this year
            elif tokPrev.lowercase in this:
                _year = ref_date.year
                named_tokens.extend([year_token, tokPrev])
            if _year is not None:
                ref_date = datetime(_year, 1, 1, 0, 0)

        for key, synonyms in self._NAMED_DATES.items():
            for synonym in synonyms:
                if synonym.lower() in tokens.lowercase:
                    regex = re.compile(r"\b%s\b(?!\')" % (synonym,), re.IGNORECASE)
                    match = regex.search(tokens.text)
                    if match:
                        named_date_tokens = tokens[match.span()]
                        named_tokens.extend(named_date_tokens)
                        tokPrev = tokens[named_date_tokens.start_index - 1]
                        tokNext = tokens[named_date_tokens.end_index + 1]
                        # last easter
                        if tokPrev.lowercase in last:
                            ref_date = ref_date - relativedelta(years=1)
                        # this easter
                        elif tokPrev.lowercase in this:
                            ref_date = datetime(ref_date.year, 1, 1, 0, 0)
                        # easter 2024
                        elif tokNext.isDigit and not tokNext.isDuration:
                            if tokNext.number < 100:
                                _year = ((ref_date.year // 100) * 100) + \
                                        tokNext.number
                            else:
                                _year = tokNext.number
                            ref_date = datetime(_year, 1, 1, 0, 0)

                        additional_dates = self.get_named_dates_local(ref_date)
                        named_dates = get_named_dates(self.lang, ref_date,
                                                      additional_dates)
                        
                        # tag as date
                        for tok in named_tokens:
                            tok.isDate = True
                        
                        # TODO: Alternatively, we could use ReplaceableEntity
                        # with custom name Flag
                        extracted_named_dates.append(ReplaceableDate(
                            named_dates[key], named_tokens)
                        )
                        break

        return extracted_named_dates
    
    def get_named_dates_local(self, ref_date: datetime) -> Dict[str, date]:
        """
        Returns a dictionary of named dates for the time period of one year since
        ref_date.

        :param ref_date (datetime): The reference date.

        :return: A dictionary of named dates.
        """
        named_dates: Dict[str, date] = dict()
        years = [ref_date.year]
        if ref_date.month != 1 or ref_date.day != 1:
            years.append(ref_date.year + 1)
        _end_date = ref_date + relativedelta(years=1, minutes=-1)

        for year in years:
            _dates = {
                "Labour Day": date(year, 9, 1),
                "Columbus Day": date(year, 10, 1),
                "Veterans Day": date(year, 11, 11),
                "Thanksgiving Day": (date(year, 11, 1) + timedelta(weeks=3, days=3 - date(year, 11, 1).weekday())),
                "Father's Day": (date(year, 6, 1) + timedelta(weeks=2, days=6 - date(year, 6, 1).weekday()))
            }

            for name, date_ in _dates.items():
                if date_ >= ref_date.date() and date_ <= _end_date.date():
                    named_dates[name] = date_

        return named_dates

    def _convert_year_abr(self, year: int, ref_date: datetime) -> Optional[int]:
        """
        Returns the year from an abbreviated year.

        :param tokens (TokenizedString): The tokenized string.
        :param ref_date (datetime): The reference date.

        :return: The year.
        """
        ref_century = (ref_date.year // 100) * 100
        ref_decade = int(str(ref_date.year)[-2:])
        # NOTE: This logigally doesn't work outside the actual cent 
        if ref_century == 2000 and year >= ref_decade + 20:
            # year belongs to last century
            # 69 -> 1969
            year = ref_century - 100 + year
        else:
            # year belongs to current century
            # 13 -> 2013
            year = ref_century + year
        return year

class GermanTimeTagger:

    _STRING_WEEKDAY = {
        "montag": 0,
        "dienstag": 1,
        "mittwoch": 2,
        "donnerstag": 3,
        "freitag": 4,
        "samstag": 5,
        "sonntag": 6,
    }
    _STRING_MONTH = {
        "jan": 1, "januar": 1, "januars": 1,
        "feb": 2, "februar": 2, "februars": 2,
        "mär": 3, "märz": 3,
        "apr": 4, "april": 4, "aprils": 4,
        "mai": 5, "mais": 5,
        "jun": 6, "juni": 6, "junis": 6,
        "jul": 7, "juli": 7, "julis": 7,
        "aug": 8, "august": 8, "augusts": 8,
        "sep": 9, "september": 9, "septembers": 9,
        "okt": 10, "oktober": 10, "oktobers": 10,
        "nov": 11, "november": 11, "novembers": 11,
        "dez": 12, "dezember": 12, "dezembers": 12
    }
    _SEASONS = {
        "frühling": Season.SPRING,
        "frühjahr": Season.SPRING,
        "sommer": Season.SUMMER,
        "herbst": Season.FALL,
        "spätjahr": Season.FALL,
        "winter": Season.WINTER
    }
    _HEMISPHERES = {
        Hemisphere.NORTH: ["nordhalbkugel", "nördliche halbkugel", "nördlichen halbkugel",
                           "nördliche hemisphäre", "nördlichen hemisphäre"],
        Hemisphere.SOUTH: ["südhalbkugel", "südliche halbkugel", "südlichen halbkugel",
                           "südliche hemisphäre", "südlichen hemisphäre"]
    }

    # mapping dictionary for alternative names of named eras
    _ERAS_SYNONYMS = {
        "AD": ["nach christus", "n. Chr.", "n.Chr.", "n. Christus", "anno domini", "a.d.",
               "a. d.", "AD", "nach unserer zeitrechnung", "nach unserer zeit", "christlicher zeitrechnung"],
        "UNIX": ["unix-zeit", "unixzeit", "unix zeit"],
        "LUCIS": ["anno lucis"],
        "ARMENIAN": ["armenischen ära", "armenische ära", "altarmenischen ära", "altarmenische ära",
                     "armenischen epoche", "armenische epoche", "altarmenischen epoche", "altarmenische epoche"],
        "THAI": ["thai kalender", "thailändischen kalenders", "thailändischen kalender",
                 "thailändischem kalender"],
        "LILIAN": ["lilianisches Datum", "lilianischen Datum", "lilianische tage", "L.D.", "L. D.", "LD",
                   "lilianische zeitrechnung"],
        "DIANETIC": ["nach dianetik"],
        "RATADIE": ["ratadie", "rata die", "r.d.", "r. d.", "RD"],
        "FASCIST": ["Faschismus", "faschistischen Ära", "faschistische Ära", "faschistischer Ära", "Era Fascista"],
        "PERSIAN": ["persischen kalender", "persische kalender", "persischem kalender",
                    "persischen ära", "persische ära", "yazdegerd ära", "yazdegerd-ära"],
        "BAHAI": ["bahai kalender", "bahai-kalender", "badi kalender", "badi-kalender", "bahai ära",
                  "bahai-ära", "badi ära", "badi-ära"],
        "JULIAN": ["julianisches Datum", "julianischen Datum", "julianischem Datum", "julianische tage",
                   "JD", "J.D.", "J. D.", "julianische zeitrechnung", "julianischen zeitrechnung"],
        "FRENCH": ["französichem republikanischen kalender", "französichen republikanischen kalender",
                   "französich republikanischen kalender", 
                   "französichen revolutionskalender", "französichem revolutions kalender"],
        "DARIAN": ["Darisches Marsjahr", "Darischen Marsjahr"],
        "POSITIVISTIC": ["positivistischen ära", "positivistische ära"],
        "ETHIOPIAN" : ["inkarnationsära", "äthiopischen ära", "äthiopische ära",
                       "äthipischer epoche", "äthiopischen epoche", "äthiopische epoche",
                       "äthipischer zeitrechnung", "äthipische zeitrechnung", "äthiopischen zeitrechnung"],
        "CHINESE-REP": ["chinesisch republikanischen ära", "Minguo-Ära", "Minguo Ära"],
        "SCHAMSI": ["hidschri schamsi", "Sonnenhidschra"],
        "QAMARI": ["hidschri qamari", "Mondhidschra"],
        "DIOCLETIAN": ["diokletianischen ära", "diokletianische ära", "diokletianischer ära",
                       "diokletianischen epoche", "diokletianische epoche", "diokletianischer epoche"],
        "BP": ["before present"]
    }

    _ARTICLES = ["der", "die", "das", "den", "dem", "des"]
    _ARTICLES_UNDET = ["einem", "einer", "eines", "einen", "eines", "einem"]
    _TIMEUNITS = ["microsekunden",
              "millisekunden",
              "sekunden",
              "minuten",
              "stunden",
              "tage",
              "wochen",
              "monate",
              "jahre",
              "jahrzehnte",
              "jahrhunderte",
              "jahrtausende",
              ]

    # mapping dictionary for alternative names of named dates
    _NAMED_DATES = {
        "New Year's Day": ["Neujahr", "neuen jahr", "neues jahr"],
        "Epiphany": ["Dreikönigstag", "Heiligen Drei Königen", "Heilige Drei Könige", "Drei Könige", "Dreikönige", "Epiphanias", "Erscheinung des Herrn"],
        "Chinese New Year": ["Chinesisches Neujahr", "Chinesischen Neujahr", "Frühlingsfest", "Yuan Tan"],
        "Valentine's Day": ["Valentinstag", "Valentine's Day"],
        "World Women's Day": ["Internationalen Frauentag", "Frauentag"],
        "St. Patrick's Day": ["Sankt Patrick's Tag", "Sankt Patricks Tag", "Skt. Patrick's Tag", "St. Patrick's Tag", "St. Patrick's Day"],
        "Meteorological Spring": ["Meteorologischer Frühling", "Meteorologischen Frühling",
                                  "Meteorologischer Frühlingsanfang", "Meteorologischen Frühlingsanfang",
                                  "Meteorologischer Frühlingsbeginn", "Meteorologischen Frühlingsbeginn"],
        "Vernal Equinox": ["Frühlingsanfang", "Frühlingsbeginn", "Frühlingsbegin"],
        "Labor Day": ["Tag der Arbeit", "Tag der Arbeiterbewegung", "Tag der Arbeiterschaft", "Tag der Arbeiter"],
        "Mother's Day": ["Muttertag"],
        "Fat Thursday": ["Weiberfastnacht"],
        "Rose Monday": ["Rosenmontag"],
        "Fat Tuesday": ["Fasching", "Fastnacht", "Karneval", "Mardi Gras",
                        "Faschingsdienstag", "Fastnachtsdienstag", "Veilchendienstag"],
        "Ash Wednesday": ["Aschermittwoch", "Lent"],
        "April Fool's Day": ["April Fools' Day", "April Fool's Day", "April Fools Day", "April Fool Day",
                             "All Fools' Day", "All Fools Day", "April Fools'", "April Fool's" , "April Fools"],
        "Palm Sunday": ["Palmsonntag"],
        "Maundy Thursday": ["Gründonnerstag"],
        "Good Friday": ["Karfreitag"],
        "Holy Saturday": ["Karsamstag"],
        "Easter Sunday": ["Ostern", "Ostersonntag", "Osterfest"],
        "Easter Monday": ["Ostermontag"],
        "Ascension Day": ["Christi Himmelfahrt", "Himmelfahrt", "Vatertag", "Herrentag", "Männertag"],
        "Pentecost": ["Pfingstsonntag", "Pfingsten"],
        "Whit Monday": ["Pfingstmontag"],
        "Corpus Christi": ["Fronleichnam", "Korpus Christi"],
        "Trinity Sunday": ["Trinitatis", "Dreifaltigkeitssonntag"],
        "Peter and Paul": ["Peter und Paul", "Peter und Paulus", "Peter und Paulstag", "Peter und Paul's Tag"],
        "Assumption of Mary": ["Mariä Himmelfahrt", "Maria Himmelfahrt"],
        "Meteorological Summer": ["Meteorologischer Sommer", "Meteorologischen Sommer",
                                 "Meteorologischer Sommeranfang", "Meteorologischen Sommeranfang",
                                 "Meteorologischer Sommerbeginn", "Meteorologischen Sommerbeginn"],
        "Summer Solstice": ["Mittsommer", "Sonnenwende", "Sommersonnenwende", "Johannisnacht", "Sankt Johannis",
                            "Sommeranfang", "Sommerbeginn"],
        "Canada Day": ["Kanada-Tag", "Canada Day", "Dominion Day"],
        "American Independence Day": ["Amerikanischer Unabhängikeitstag", "Amerikanischen Unabhängikeitstag",
                                      "Amerikanischer Nationalfeiertag", "Amerikanischen Nationalfeiertag"],
        "Bastille Day": ["French National Day", "Bastille Day"],
        "International Friendship Day": ["Friendship Day", "International Friendship Day"],
        "Oktoberfest": ["Oktoberfest"],
        "Meteorological Fall": ["Meteorologischer Herbst", "Meteorologischen Herbst",
                                "Meteorologischer Herbstanfang", "Meteorologischen Herbstanfang",
                                "Meteorologischer Herbstbeginn", "Meteorologischen Herbstbeginn"],
        "Autumnal Equinox": ["Herbstanfang", "Herbstbeginn", "Herbstbegin"],
        "German Unity Day": ["Tag der Deutschen Einheit", "Deutsche Einheit", "Deutschen Einheit"],
        "Halloween": ["Halloween", "Allerheiligenabend", "Reformationstag"],
        "All Saints' Day": ["Allerheiligen", "Aller Heiligen"],
        "All Souls' Day": ["Allerseelen", "Aller Seelen"],
        "Thanksgiving Day": ["Thanksgiving"],
        "Erntedank": ["Erntedankfest", "Erntedank"],
        "Hanukkah": ["Chanukah", "Hanukkah"],
        "St. Martin's Day": ["Martinstag", "Sankt Martin", "Sankt Martinstag", "Sankt Martin's Tag"],
        "St. Nicholas Day": ["Nikolaus", "Nikolaustag"],
        "Volkstrauertag": ["Volkstrauertag"],
        "Buß- und Bettag": ["Buß- und Bettag", "Buß und Bettag", "Buss und Bettag"],
        "Meteorological Winter": ["Meteorologischer Winter", "Meteorologischen Winter",
                                  "Meteorologischer Winteranfang", "Meteorologischen Winteranfang",
                                  "Meteorologischer Winterbeginn", "Meteorologischen Winterbeginn"],
        "Totensonntag": ["Totensonntag", "Ewigkeitssonntag"],
        "Winter Solstice": ["Wintersonnenwende", "Winteranfang"],
        "1st Advent": ["1. Advent", "1. Sonntag im Advent", "1. Adventssonntag", "1. Adventsonntag", "Advent"],
        "2nd Advent": ["2. Advent", "2. Sonntag im Advent", "2. Adventssonntag", "2. Adventsonntag"],
        "3rd Advent": ["3. Advent", "3. Sonntag im Advent", "3. Adventssonntag", "3. Adventsonntag"],
        "4th Advent": ["4. Advent", "4. Sonntag im Advent", "4. Adventssonntag", "4. Adventsonntag"],
        "Christmas Eve": ["Heiligabend", "Weihnachten"],
        "Christmas Day": ["1. Weihnachtsfeiertag", "1. Weihnachtstag"],
        "Boxing Day": ["2. Weihnachtsfeiertag", "2. Weihnachtstag", "Stephans Tag", "Stephan's Tag", "Stephanstag"],
        "Kwanzaa": ["Kwanza", "Kwanzaa"],
        "New Year's Eve": ["Sylvester", "Silvester"],
        "World Women’s Day": ["Weltfrauentag", "Internationaler Frauentag", "Frauentag"],
        "World Health Day": ["Weltgesundheitstag"],
        "World Earth Day": ["Tag der Erde"],
        "World Fair Trade Day": ["Welttag des fairen Handels", "Fair Trade Day"],
        "World No Tobacco Day": ["Weltnichtrauchertag", "Anti-Tabak-Tag"],
        "World Children's Day": ["Weltkindertag",  "Internationaler Kindertag", "Internationalen Kindertag"],
        "World Oceans Day": ["Welttag der Ozeane", "Tag der Meere"],
        "World Blood Donation Day": ["Weltblutspendetag"],
        "World Population Day": ["Weltbevölkerungstag"],
        "World Youth Skills Day": ["Internationaler Tag der Jugendkompetenzen", "Tag der Jugendfähigkeiten"],
        "World Hepatitis Day": ["Welt-Hepatitis-Tag"],
        "World Breastfeeding Week": ["Weltstillwoche", "Internationale Woche des Stillens"],
        "World Humanitarian Day": ["Welttag der humanitären Hilfe", "Humanitärer Tag", "Humanitären Tag"],
        "World Alzheimer’s Day": ["Welt-Alzheimertag", "Alzheimer-Tag"],
        "World Tourism Day": ["Welttourismustag", "Tourismus-Tag"],
        "World Vegetarian Day": ["Weltvegetariertag", "Vegetariertag"],
        "World Animal Day": ["Welttierschutztag", "Tierschutztag"],
        "World Mental Health Day": ["Welttag der psychischen Gesundheit", "Psychische Gesundheit Tag"],
        "World Food Day": ["Welternährungstag", "Ernährungstag"],
        "World Osteoporosis Day": ["Weltosteoporosetag", "Osteoporosetag"],
        "World Television Day": ["Weltfernsehtag", "Fernsehtag"],
        "World AIDS Day": ["Weltaidstag", "Aidstag"],
        "World Soil Day": ["Weltbodentag", "Bodentag"],
    }

    lang = "de-de"

    def extract_named_dates(self, data: Union[str, Tokens],
                                  ref_date: Optional[datetime] = None) \
        -> List[ReplaceableDate]:
        """
        Returns a alist of named dates if found in the text.
        """
        ref_date = ref_date or now_local()
        extracted_named_dates = []
        named_tokens = []

        if isinstance(data, str):
            tokens = Tokens(data, self.lang)
        else:
            tokens = data

        # NOTE: the tricky thing here is
        # * variable dates like easter,.. (ie. you cant do easter - 1 year)
        # * easter last year/.. years ago (fixed), last easter (dependent on when you ask)
        
        upcoming = ["nächste", "nächstem", "nächsten", "nächstes", "nächster",
                    "kommende", "kommendem", "kommenden", "kommendes", "kommender"]
        last = ["letzte", "letztem", "letzten", "letztes", "letzter"]
        this = ["diese", "dieses", "diesem", "dieser", "diesen",
                "aktuell", "aktuelle", "aktuellen", "aktueller", "aktuelles",
                "gegenwärtig", "gegenwärtige", "gegenwärtigen", "gegenwärtiger", "gegenwärtiges",
                "momentan", "momentane", "momentanen", "momentaner", "momentanes"]
                
        # parse the year from the utterance
        year_token = tokens.find(["jahr", "jahre", "jahren", "jahres"])
        _year = None
        if year_token:
            tokNext = tokens[year_token.index + 1]
            tokPrev = tokens[year_token.index - 1]
            tokPrevPrev = tokens[year_token.index - 2]
            if year_token.isDuration and tokPrev.isDigit \
                    and tokPrevPrev.lowercase in ["vor", "in"]:
                if tokPrevPrev.lowercase == "vor":
                    _year = ref_date.year - tokPrev.number
                    named_tokens.extend([year_token, tokPrev, tokPrevPrev])
                elif tokPrevPrev.lowercase == "in":
                    _year = ref_date.year + tokPrev.number
                    named_tokens.extend([year_token, tokPrev, tokPrevPrev])
            elif tokNext.isDigit:
                if tokNext.number < 100:
                    _year = ((ref_date.year // 100) * 100) + tokNext.number
                else:
                    _year = tokNext.number
                named_tokens.extend([year_token, tokNext])
            elif tokPrev.lowercase in last:
                _year = ref_date.year - 1
                named_tokens.extend([year_token, tokPrev])
            elif tokPrev.lowercase in upcoming:
                _year = ref_date.year + 1
                named_tokens.extend([year_token, tokPrev])
            elif tokPrev.lowercase in this:
                _year = ref_date.year
                named_tokens.extend([year_token, tokPrev])
            if _year is not None:
                ref_date = datetime(_year, 1, 1, 0, 0)

        for key, synonyms in self._NAMED_DATES.items():
            for synonym in synonyms:
                if synonym.lower() in tokens.lowercase:
                    regex = re.compile(r"\b%s[s]?\b(?!\')" % (synonym,), re.IGNORECASE)
                    match = regex.search(tokens.text)
                    if match:
                        named_date_tokens = tokens[match.span()]
                        named_tokens.extend(named_date_tokens)
                        tokPrev = tokens[named_date_tokens.start_index - 1]
                        tokNext = tokens[named_date_tokens.end_index + 1]
                        # letzte Ostern
                        if tokPrev.lowercase in last:
                            ref_date = ref_date - relativedelta(years=1)
                        # diese Ostern
                        elif tokPrev.lowercase in this:
                            ref_date = datetime(ref_date.year, 1, 1, 0, 0)
                        # Ostern 2024
                        elif tokNext.isDigit:
                            if tokNext.number < 100:
                                _year = ((ref_date.year // 100) * 100) + \
                                        tokNext.number
                            else:
                                _year = tokNext.number
                            ref_date = datetime(_year, 1, 1, 0, 0)

                        additional_dates = self.get_named_dates_local(ref_date)
                        named_dates = get_named_dates(self.lang, ref_date,
                                                      additional_dates)
                        
                        # tag as date
                        for tok in named_tokens:
                            tok.isDate = True
                        
                        # TODO: Alternatively, we could use ReplaceableEntity
                        # with custom name Flag
                        extracted_named_dates.append(ReplaceableDate(
                            named_dates[key], named_tokens)
                        )
                        break

        return extracted_named_dates
    
    def get_named_dates_local(self, ref_date: datetime) -> Dict[str, date]:
        """
        Returns a dictionary of named dates for a time period of 1 year since ref_date.

        :param ref_date: reference date
        :type ref_date: datetime

        :return: dictionary of named dates
        """
        named_dates: Dict[str, date] = dict()
        years = [ref_date.year]
        if ref_date.month != 1 or ref_date.day != 1:
            years.append(ref_date.year + 1)
        _end_date = ref_date + relativedelta(years=1, minutes=-1)

        for year in years:
            easter_sunday = easter(year)
            _dates = {"Fat Thursday": easter_sunday - timedelta(days=52),
                      "Rose Monday": easter_sunday - timedelta(days=48),
                      "St. Martin's Day": date(year, 11, 11),
                      "Oktoberfest": (date(year, 9, 1) + timedelta(weeks=2, days=5 - date(year, 9, 1).weekday())),
                      "Labor Day": date(year, 5, 1),
                      "Erntedank": date(year, 10, 1) + timedelta(days=(6 - date(year, 10, 1).weekday()) % 7),
                      "Volkstrauertag": date(year, 11, 1) + timedelta(weeks=2, days=6 - date(year, 11, 1).weekday()),
                      "Totensonntag": date(year, 11, 1) + timedelta(weeks=3, days=0 - date(year, 11, 1).weekday()),
                      "Buß- und Bettag": date(year, 11, 1) + timedelta(weeks=3, days=2 - date(year, 11, 1).weekday())}
            
            for name, date_ in _dates.items():
                if date_ >= ref_date.date() and date_ <= _end_date.date():
                    named_dates[name] = date_

        return named_dates
    
    def extract_date(self, text: str,
                           ref_date: Optional[datetime] = None,
                           resolution: DateTimeResolution = DateTimeResolution.DAY,
                           hemisphere: Optional[Hemisphere] = None,
                           location_code: Optional[str] = None,
                           greedy: bool = False,

                           ) -> Optional[ReplaceableDate]:
        """
        Extracts date information from a sentence.  Parses many of the
        common ways that humans express dates and times, including relative dates
        like "5 days from today", "tomorrow', and "Tuesday".

        Args:
            text (str): the text to be interpreted
            anchorDate (:obj:`datetime`, optional): the date to be used for
                relative dating (for example, what does "tomorrow" mean?).
                Defaults to the current local date/time.
        Returns:
            extracted_date (datetime.date): 'date' is the extracted date as a datetime.date object.
                Returns 'None' if no date related text is found.

        Examples:

            >>> extract_datetime(
            ... "What is the weather like the day after tomorrow?",
            ... datetime(2017, 6, 30, 00, 00)
            ... )
            datetime.date(2017, 7, 2)

            >>> extract_datetime(
            ... "Set up an appointment 2 weeks from Sunday at 5 pm",
            ... datetime(2016, 2, 19, 00, 00)
            ... )
            datetime.date(2016, 3, 6)

            >>> extract_datetime(
            ... "Set up an appointment",
            ... datetime(2016, 2, 19, 00, 00)
            ... )
            None
        """
        replaceable_datetime = self.extract_datetime(text,
                                                     ref_date=ref_date,
                                                     resolution=resolution,
                                                     hemisphere=hemisphere,
                                                     location_code=location_code,
                                                     date_only=True,
                                                     greedy=greedy)
        if replaceable_datetime:
            date_tokens = [token for token in replaceable_datetime]  # if token.isDate or token.isDuration
            return ReplaceableDate(replaceable_datetime.value.date(), date_tokens)
        return None

    def extract_time(self, text: str,
                           ref_date: Optional[datetime] = None,
                           resolution: DateTimeResolution = DateTimeResolution.SECOND,
                           hemisphere: Optional[Hemisphere] = None,
                           location_code: Optional[str] = None,
                           ) -> Optional[ReplaceableTime]:
        """
        Extracts time information from a sentence.  Parses many of the
        common ways that humans express dates and times".

        Vague terminology are given arbitrary values, like:
            - morning = 8 AM
            - afternoon = 3 PM
            - evening = 7 PM

        If a time isn't supplied or implied, the function defaults to 12 AM

        Args:
            text (str): the text to be interpreted
            anchorDate (:obj:`datetime`, optional): the date to be used for
                relative dating (for example, what does "tomorrow" mean?).
                Defaults to the current local date/time.
        Returns:
            extracted_time (datetime.time): 'time' is the extracted time
                as a datetime.time object in the anchorDate (or default if None) timezone.
                Returns 'None' if no time related text is found.

        Examples:

            >>> extract_time(
            ... "What is the weather like the day after tomorrow?"
            ... )
            datetime.time(0, 0, 0)

            >>> extract_time(
            ... "Set up an appointment 2 weeks from Sunday at 5 pm"
            ... )
            datetime.time(17, 0, 0)

            >>> extract_datetime(
            ... "Set up an appointment"
            ... )
            None
        """
        replaceable_datetime = self.extract_datetime(text,
                                                     ref_date=ref_date,
                                                     resolution=resolution,
                                                     hemisphere=hemisphere,
                                                     location_code=location_code)
        if replaceable_datetime:
            time_tokens = [token for token in replaceable_datetime if token.isTime or token.isDuration]
            return ReplaceableTime(replaceable_datetime.value.time(), time_tokens)
        return None
    
    def extract_datetime(self, data: Union[str, Tokens],
                               ref_date: Optional[datetime] = None,
                               resolution: DateTimeResolution = DateTimeResolution.SECOND,
                               hemisphere: Optional[Hemisphere] = None,
                               location_code: Optional[str] = None,
                               date_only: bool = False,
                               greedy: bool = False):

        ref_date = ref_date or now_local()

        past_qualifiers = ["vor", "früher", "davor", "vorher", "zuvor"]
        #future_qualifiers?
        relative_qualifiers = ["in", "vor", "nach", "seit", "ab", 
                               "früher", "davor", "vorher", "zuvor"]  # , "von"
        # TODO von/vom
        of_qualifiers = ["im", "in", "des", "der"]  # {Nth} day/week/month.... of month/year/century.. 
        set_qualifiers = ["ist", "war"]  # "the year is 2021"
        # time
        daytimes = {"früh": (3,0),
                    "morgen": (6,0), "morgens": (6,0),
                    "vormittag": (9,0), "vormittags": (9,0),
                    "mittag": (12,0), "mittags": (12,0),
                    "nachmittag": (15,0), "nachmittags": (15,0),
                    "abend": (18,0), "abends": (18,0),
                    "nacht": (21,0), "nachts": (21,0),
                    "mitternacht": (0,0), "mitternachts": (0,0)}        
        same_day_marker = ["heute", "heutigen", "heutigem", "heutiges", "heutiger", "heutige"]
        pm_markers = ["nachmittag", "nachmittags", "abend", "abends", "nacht", "nachts", "pm",
                      "p.m.", "P.M.", "PM"]
        daytime_night = ["nacht", "nachts"]
        near_dates = {"jetzt": 0, "jetzigen": 0, "jetzigem": 0, "jetziges": 0, "jetziger": 0, "jetzige": 0,
                      "heute": 0, "heutigen": 0, "heutigem": 0, "heutiges": 0, "heutiger": 0, "heutige": 0,
                      "gestern": -1, "gestrigen": -1, "gestrigem": -1, "gestriges": -1, "gestriger": -1, "gestrige": -1,
                      "vorgestern": -2, "vorgestrigen": -2, "vorgestrigem": -2, "vorgestriges": -2, "vorgestriger": -2,
                      "morgen": 1, "morgigen": 1, "morgigem": 1, "morgiges": 1, "morgiger": 1, "morgige": 1,
                      "übermorgen": 2, "übermorgigen": 2, "übermorgigem": 2, "übermorgiges": 2, "übermorgiger": 2,
                      "übermorgige": 2}

        more_markers = ["weitere", "weiterem", "weiteren", "weiteres", "weiterer",
                        "zusätzliche", "zusätzlichem", "zusätzlichen", "zusätzliches", "zusätzlicher"]
        less_markers = ["minus"]
        future_markers = ["nächste", "nächstem", "nächsten", "nächstes", "nächster",
                          "kommende", "kommendem", "kommenden", "kommendes", "kommender"]
        time_markers = ['um']
        date_markers = ['am', "dem"]

        this = ["diese", "dieses", "diesem", "dieser", "diesen",
                "aktuell", "aktuelle", "aktuellen", "aktueller", "aktuelles",
                "gegenwärtig", "gegenwärtige", "gegenwärtigen", "gegenwärtiger", "gegenwärtiges",
                "momentan", "momentane", "momentanen", "momentaner", "momentanes"]  # check
        mid = ["mitte", "mitten"]
        begin = ['begin', 'beginn', 'anfang']
        end = ['ende']
        last = ["letzte", "letztem", "letzten", "letztes", "letzter"]

        clock_markers = ["uhr", "AM", "PM", "am", "pm",
                         "p.m.", "a.m.", "P.M.", "A.M."]
        day_literal = ["tag", "tage", "tages"]
        weekday_literals = ["montag", "dienstag", "mittwoch", "donnerstag", "freitag", "samstag", "sonntag",
                             "montags", "dienstags", "mittwochs", "donnerstags", "freitags", "samstags", "sonntags"]
        week_literal = ["woche", "wochen"]
        weekend_literal = ["wochenende", "wochenenden", "wochenendes"]
        month_literal = ["monat", "monate", "monaten", "monats"]
        year_literal = ["jahr", "jahre", "jahren", "jahres"]
        century_literal = ["jahrhundert", "jahrhunderte",
                        "jahrhunderten", "jahrhunderts"]
        decade_literal = ["jahrzehnt", "jahrzehnte", "jahrzehnten", "jahrzehnts"]
        millennium_literal = ["millennium", "millennia", "millennien", "millenniums",
                              "jahrtausend", "jahrtausende", "jahrtausenden", "jahrtausends"]
        season_markers = ["frühling", "frühjahr", "sommer", "herbst", "spätjahr", "winter",
                          "frühlings", "frühjahrs", "sommers", "herbsts", "spätjahrs", "winters"]
        dateunit_literals = day_literal + week_literal + weekend_literal + \
            month_literal + year_literal + century_literal + decade_literal + \
            millennium_literal
        season_literal = ["saison", "säson", "jahreszeit"]

        def _to_datetime_resolution(dateunit: str) -> DateTimeResolution:
            if dateunit in day_literal:
                return DateTimeResolution.DAY
            elif dateunit in week_literal:
                return DateTimeResolution.WEEK
            elif dateunit in weekend_literal:
                return DateTimeResolution.WEEKEND
            elif dateunit in month_literal:
                return DateTimeResolution.MONTH
            elif dateunit in year_literal:
                return DateTimeResolution.YEAR
            elif dateunit in century_literal:
                return DateTimeResolution.CENTURY
            elif dateunit in decade_literal:
                return DateTimeResolution.DECADE
            elif dateunit in millennium_literal:
                return DateTimeResolution.MILLENNIUM
            else:
                raise ValueError("Unknown dateunit: {}".format(dateunit))

        if isinstance(data, str):
            date_words = GermanNumberParser().convert_words_to_numbers(data,
                                                                       ordinals=True)
            self._tag_durations(date_words)
        else:
            date_words = data

        extracted_date: Optional[datetime] = None
        delta: Union[timedelta, relativedelta] = timedelta(0)
        _delta: Optional[ReplaceableTimedelta] = None  # Timedelta Tokens
        date_found: bool = False
        
        time_found: bool = False
        _hour: Optional[int] = None
        _min: Optional[int] = None
        
        if hemisphere is None:
            hemisphere = self.extract_hemisphere(date_words) \
                         or get_active_hemisphere()
        
        # time parsing
        # # TODO: 12:00:00
        is_pm = any(token.word in pm_markers for token in date_words)
        used_pm_marker = [token.word.lower() for token in date_words
                          if token.word in pm_markers]
        
        if not date_only:
            ambiguous_time = True
            _earlier = ["vor"]
            _later = ["nach"]
            for token in date_words:
                if token.isConsumed or token.isSymbolic:
                    continue
                _consumed = []

                # empty Token if oob
                tokPrevPrev = date_words[token.index - 2]
                tokPrev = date_words[token.index - 1]
                tokNext = date_words[token.index + 1]
                tokNextNext = date_words[token.index + 2]

                if ":" in token.word or \
                        ("." in token.word and token.isNumeric and
                         tokNext.lowercase in clock_markers):
                    for components in [token.word.split(marker)
                                       for marker in (":", ".")]:
                        if len(components) == 2 and \
                                all(map(str.isdigit, components)) and\
                                int(components[0]) < 25 and int(components[1]) < 60:
                            _hstr, _mstr = components
                            _mstr = _mstr.ljust(2, "0")
                            _hour = int(_hstr)
                            _min = int(_mstr)
                            _consumed.append(token)
                            ambiguous_time = False
                # parse {fraction/number} vor/nach {HH}, eg. viertel vor 12, 10 nach 12 (12-hour format)
                # has to be used with pm qualifier (eg. nachmittags) to be used in 24-hour format
                elif all([token.isNumeric and token.number <= 30,
                          tokNext.word in _earlier + _later,
                          tokNextNext.isDigit and tokNextNext.number <= 12]):
                    _minutes = token.number*60 if token.number < 1 else token.number
                    if tokNext.lowercase in _earlier:
                        _hour = tokNextNext.number - 1
                        _min = 60 - _minutes
                    else:
                        _hour = tokNextNext.number
                        _min = _minutes
                    _consumed.extend([token, tokNext, tokNextNext])
                    ambiguous_time = False
                # parse {HH} uhr, {HH} uhr {MM}, {HH} {MM} a.m.
                elif token.lowercase in clock_markers:
                    if ambiguous_time:
                        if tokPrevPrev.isDigit and tokPrevPrev.number < 25 \
                                and tokPrev.isDigit and tokPrev.number < 60:
                            _hour = tokPrevPrev.number
                            _min = tokPrev.number
                            _consumed.extend([tokPrevPrev, tokPrev, token])
                            ambiguous_time = False
                        elif tokPrev.isDigit and tokPrev.number < 25:
                            _hour = tokPrev.number
                            _consumed.extend([tokPrev, token])
                            if tokNext.isDigit and tokNext.number < 60:
                                _min = tokNext.number
                                _consumed.append(tokNext)
                            ambiguous_time = False
                    else:
                        _consumed.append(token)
                # parse (um) {HH} {MM}, (um) {HH} (standalone)
                # TODO military time?
                elif all([token.isDigit and token.number < 24,
                          tokPrev.lowercase in time_markers,  
                          not tokNext.lowercase in clock_markers]):
                    _hour = token.number
                    _consumed.append(token)
                    if tokNext.isDigit and tokNext.number < 60:
                        _min = tokNext.number
                        _consumed.append(tokNext)
                # parse morning/afternoon/evening/night/noon/midnight
                elif token.lowercase in daytimes:
                    if token.lowercase == "morgen" and tokPrev.lowercase != "am":
                        continue
                    if not time_found:
                        _hour, _min = daytimes[token.lowercase]
                    _consumed.append(token)

                if _hour is not None:
                    _hour += 12 if is_pm and _hour < 12 and not \
                        (any(marker in used_pm_marker for marker in daytime_night)
                         and _hour < 6) else 0
                    _min = 0 if _min is None else _min
                    time_found = True
                
                for tok in _consumed:
                    tok.isTime = True
                    tok.isConsumed = True

        ## date parsing

        # Preprocess named dates and named eras
        # named dates, "ostern, letzte ostern, ostern 2023, ostern in einem jahr, .."
        named_dates: List[ReplaceableDate] = self.extract_named_dates(date_words, ref_date)
        named_date = named_dates[0] if named_dates else None
        if named_date:
            for tok in named_date:
                date_words.consume(tok)
                    
        # named_eras, ".. nach christus, ..."
        named_era = None
        for era, era_date in _NAMED_ERAS.items():
            for syn in self._ERAS_SYNONYMS[era]:
                if syn.lower() in date_words.lowercase:
                    regex = re.compile(r"\b%s[s]?(?:(?<=\.)|(?<=\b))" % (syn,), re.IGNORECASE)
                    match = regex.search(date_words.text)
                    if match:
                        named_era_tokens = date_words[match.span()]
                        for tok in named_era_tokens:
                            date_words.consume(tok)
                        if era == "UNIX":
                            resolution = DateTimeResolution.UNIX
                        elif era == "LILIAN":
                            resolution = DateTimeResolution.LILIAN
                        elif era == "JULIAN":
                            resolution = DateTimeResolution.JULIAN
                        elif era == "RATADIE":
                            resolution = DateTimeResolution.RATADIE
                        
                        named_era = ReplaceableDate(era_date, named_era_tokens)
                        break

        # is this a negative timespan?
        # past_tok = date_words.find(past_qualifiers)
        # is this relative to a date (or time)?
        relative_tok = date_words.find(relative_qualifiers, allow_consumed=False)
        is_relative_past = relative_tok.lowercase in past_qualifiers \
            if relative_tok else False
        # is this a timespan in the future/past?
        math_tok = date_words.find(more_markers+less_markers, allow_consumed=False)
        is_sum = math_tok.word in more_markers if math_tok else False
        is_subtract = math_tok.word in less_markers if math_tok else False
        
        # dritter tag im monat mai / letzter montag im mai
        of_tok = date_words.find(of_qualifiers, allow_consumed=False)
        # exclude dates; fünfter mai im jahr ...
        # exclude durations; in 3 tagen
        if of_tok: 
            if date_words[of_tok.index - 1].lowercase in self._STRING_MONTH \
                    or any(token.isDuration for token in date_words) \
                    or date_words[of_tok.index - 1].lowercase in begin + mid + end:
                of_tok = None       
        
        if of_tok and not date_found:

            following_tok = date_words[of_tok.index + 1:]
            # limit to max. 3 tokens
            preceding_tok = date_words[of_tok.index-4:of_tok.index]

            _last_of = preceding_tok.find(last + end)
            
            _resolutions = dict()
            _ref_day = None  # TODO rename to weekday_info or else
            _anchor_date = None

            # Defaults
            _unit = "tag"
            _res = DateTimeResolution.DAY_OF_MONTH

            _ordinal = preceding_tok.find_tag("isOrdinal")
            _number = _ordinal.number if _ordinal else None
            # parse "{ORDINAL} {tag/<wochentag>/woche/monat/jahr...} im ..."
            # TODO do away with this case
            if len(preceding_tok) > 1:
                _unit_tok = preceding_tok.find(dateunit_literals + \
                                               weekday_literals)

                if _last_of:
                    _number = -1
                    date_words.consume(_last_of)
                if _unit_tok:
                    _unit = _unit_tok.lowercase
                    # dienstag -> 2. tag (nur wenn nicht "2. dienstag")
                    if _unit in weekday_literals and _number is None:
                        _number = self._STRING_WEEKDAY[_unit.rstrip("s")] + 1
                        _unit = "tag"
                    if _number:
                        date_words.consume(_unit_tok)

            # parse "{NUMBER}"
            elif len(preceding_tok) == 1 and _number:
                date_words.consume(_ordinal)
            
            # parse {reference_date}
            _replaceable_date = self.extract_datetime(following_tok,
                                                      ref_date,
                                                      resolution,
                                                      hemisphere,
                                                      date_only=True)

            # update consumed words
            if _replaceable_date:
                for tok in _replaceable_date:
                    date_words.consume(tok)
                _anchor_date = _replaceable_date.value

            # parse resolution {X} {day/week/month/year...} of {Y}
            if _number:
                # year is normally not spoken
                _request_year = False

                # TODO irrelevant?
                # parse "Nth {day/week/month/year...} of {YEAR}"
                if following_tok and date_words[of_tok.index+1].isDigit:
                    _request_year = True
                    _res = DateTimeResolution.DAY_OF_YEAR

                # parse "{NUMBER} day" or "{NUMBER} saturday"
                if _unit in day_literal or _unit in weekday_literals:
                    # "... of Y" (get the overall resolution)
                    _ref_day = self._STRING_WEEKDAY.get(_unit.rstrip("s"))
                    _resolutions = {
                        DateTimeResolution.DAY_OF_WEEK: week_literal,
                        DateTimeResolution.DAY_OF_MONTH: month_literal + \
                                                         list(self._STRING_MONTH.keys()),
                        DateTimeResolution.DAY_OF_YEAR: year_literal,
                        DateTimeResolution.DAY_OF_DECADE: decade_literal,
                        DateTimeResolution.DAY_OF_CENTURY: century_literal,
                        DateTimeResolution.DAY_OF_MILLENNIUM: millennium_literal,
                        DateTimeResolution.DAY_OF_SEASON: season_markers
                        }
                    # default
                    # TODO DateTimeResolution.DAY schould be better since it is countig from ref_date
                    # and not computing start of month/year/...
                    if not _request_year:
                        _res = DateTimeResolution.DAY_OF_REFERENCE
                    else:
                        _res = DateTimeResolution.DAY_OF_YEAR

                # parse "{NUMBER} week
                elif _unit in week_literal:
                    # "... of Y" (get the overall resolution)
                    _resolutions = {
                        DateTimeResolution.WEEK_OF_MONTH: month_literal + \
                                                          list(self._STRING_MONTH.keys()),
                        DateTimeResolution.WEEK_OF_YEAR: year_literal,
                        DateTimeResolution.WEEK_OF_DECADE: decade_literal,
                        DateTimeResolution.WEEK_OF_CENTURY: century_literal,
                        DateTimeResolution.WEEK_OF_MILLENNIUM: millennium_literal,
                        DateTimeResolution.WEEK_OF_SEASON: season_markers
                        }

                    if _request_year:
                        _res = DateTimeResolution.WEEK_OF_YEAR
                    else:
                        _res = DateTimeResolution.WEEK_OF_REFERENCE
                
                elif _unit in weekend_literal:
                    # "... of Y" (get the overall resolution)
                    _resolutions = {
                        DateTimeResolution.WEEKEND_OF_MONTH: month_literal + \
                                                             list(self._STRING_MONTH.keys()),
                        DateTimeResolution.WEEKEND_OF_YEAR: year_literal
                        }

                    if _request_year:
                        _res = DateTimeResolution.WEEKEND_OF_YEAR
                    else:
                        _res = DateTimeResolution.WEEKEND_OF_MONTH

                # parse "{NUMBER} month:
                elif _unit in month_literal:
                    # "... of Y" (get the overall resolution)
                    _resolutions = {
                        DateTimeResolution.MONTH_OF_YEAR: year_literal,
                        DateTimeResolution.MONTH_OF_DECADE: decade_literal,
                        DateTimeResolution.MONTH_OF_CENTURY: century_literal,
                        DateTimeResolution.MONTH_OF_MILLENNIUM: millennium_literal,
                        DateTimeResolution.MONTH_OF_SEASON: season_markers
                        }
                    # TODO DateTimeResolution.MONTH?
                    if _request_year:
                        _res = DateTimeResolution.MONTH_OF_YEAR
                    else:
                        _res = DateTimeResolution.MONTH_OF_REFERENCE

                # parse "{NUMBER} year
                elif _unit in year_literal:
                    # "... of Y" (get the overall resolution)
                    _resolutions = {
                        DateTimeResolution.YEAR_OF_DECADE: decade_literal,
                        DateTimeResolution.YEAR_OF_CENTURY: century_literal,
                        DateTimeResolution.YEAR_OF_MILLENNIUM: millennium_literal
                        }

                    _res = DateTimeResolution.YEAR_OF_REFERENCE

                # parse "{NUMBER} decade
                elif _unit in decade_literal:
                    _resolutions = {
                        DateTimeResolution.DECADE_OF_CENTURY: century_literal,
                        DateTimeResolution.DECADE_OF_MILLENNIUM: millennium_literal
                        }

                    _res = DateTimeResolution.DECADE_OF_REFERENCE

                # parse "{NUMBER} century
                elif _unit in century_literal:
                    _resolutions = {
                        DateTimeResolution.CENTURY_OF_MILLENNIUM: millennium_literal
                        }

                    _res = DateTimeResolution.CENTURY_OF_REFERENCE

                # parse "{NUMBER} millennium
                elif _unit in millennium_literal:
                    _res = DateTimeResolution.MILLENNIUM_OF_REFERENCE
                
                # check _following_words to find the complete resolution
                for _resolution, _res_words in _resolutions.items():
                    _res_tok = following_tok.find(_res_words)
                    if _res_tok:
                        _res = _resolution
                        break

            # compute date in reference to resolution
            if _number and _anchor_date:
                date_found = True
                extracted_date = get_date_ordinal(_number, _ref_day,
                                                  _anchor_date, _res)
                date_words.consume(of_tok)

            # Parse {partial_date} of {partial_reference_date}
            # "Sommer des Jahres 1969"
            elif _anchor_date:
                _partial_date = self.extract_datetime(preceding_tok,
                                                      _anchor_date,
                                                      resolution,
                                                      hemisphere,
                                                      date_only=True)

                if _partial_date:
                    date_found = True
                    extracted_date = _partial_date.value
                    date_words.consume(of_tok)

                    for tok in _partial_date:
                        date_words.consume(tok)
                else:
                    date_found = True
                    extracted_date = _anchor_date
        
        if relative_tok and not date_found:

            preceding_tok = date_words[:relative_tok.index]
            following_tok = date_words[relative_tok.index + 1:]

            _anchor_date = None
            _resolution = None
            _offset = timedelta(0)

            if any(tok.isDuration for tok in preceding_tok):
                deltas  = self.extract_durations(preceding_tok,
                                                 resolution=DurationResolution.RELATIVEDELTA_FALLBACK)

                if deltas:
                    _delta = deltas[-1]
                    date_words.consume([relative_tok] + _delta.tokens)
                    _offset = _delta.value
                    if is_relative_past:
                        _offset *= -1
            elif preceding_tok:
                replaceable_date = self.extract_datetime(preceding_tok,
                                                          ref_date,
                                                          resolution,
                                                          hemisphere,
                                                          date_only=True)
                if replaceable_date:
                    for tok in replaceable_date:
                        date_words.consume(tok)
                    extracted_date = replaceable_date.value

            if any(tok.isDuration for tok in following_tok):
                _delta = self.extract_durations(following_tok,
                                                resolution=DurationResolution.RELATIVEDELTA_FALLBACK)[0]
                _offset = _delta.value
                if is_relative_past:
                    _offset *= -1
                date_words.consume(_delta.tokens)

                replaceable_date = self.extract_datetime(following_tok,
                                                          ref_date,
                                                          resolution,
                                                          hemisphere,
                                                          date_only=True)
                if replaceable_date:
                    for tok in replaceable_date:
                        date_words.consume(tok)
                    extracted_date = replaceable_date.value
            else:
                _replaceable_date = self.extract_datetime(following_tok,
                                                          ref_date,
                                                          hemisphere=hemisphere,
                                                          date_only=True)
                if _replaceable_date is None and following_tok:
                    _year = following_tok.tokens[0]
                    if _year.isDigit and len(_year.word) == 4:
                        _anchor_date = datetime(day=1,
                                                month=1,
                                                year=_year.number,
                                                tzinfo=ref_date.tzinfo)
                        _resolution = DateTimeResolution.YEAR
                        date_words.consume(_year)
                elif _replaceable_date:
                    # update consumed words
                    for tok in _replaceable_date:
                        date_words.consume(tok)
                    _anchor_date = _replaceable_date.value

                _dateunit_tok = following_tok.find(dateunit_literals + \
                                               list(self._STRING_MONTH.keys()) + \
                                               list(self._STRING_WEEKDAY.keys()) + \
                                               list(near_dates.keys()))

                if _dateunit_tok:
                    _dateunit = _dateunit_tok.lowercase.rstrip('s')
                    if _dateunit not in dateunit_literals:
                        if _dateunit in self._STRING_MONTH and _anchor_date and \
                                not any(_anchor_date.day == t.number for t in following_tok):
                            _dateunit = "month"
                        else:
                            _dateunit = "day"
                    _resolution = DateTimeResolution[_dateunit.upper()]

                ref_date = _anchor_date or ref_date


                # after/before
                # .. day
                if _resolution == DateTimeResolution.DAY:
                    extracted_date = ref_date
                # .. week
                elif _resolution == DateTimeResolution.WEEK:
                    if not is_relative_past:
                        _, extracted_date = get_week_range(ref_date)
                    # NOTE: a request of {dateunit} (usually) comes back at the 
                    # beginning of that unit range 
                    else:
                        extracted_date = ref_date
                # .. month
                elif _resolution == DateTimeResolution.MONTH:
                    if not is_relative_past:
                        _, extracted_date = get_month_range(ref_date)
                    else:
                        extracted_date = ref_date
                # .. year
                elif _resolution == DateTimeResolution.YEAR:
                    if not is_relative_past:
                        _, extracted_date = get_year_range(ref_date)
                    else:
                        extracted_date = ref_date
                # .. decade
                elif _resolution == DateTimeResolution.DECADE:
                    if not is_relative_past:
                        _, extracted_date = get_decade_range(ref_date)
                    else:
                        extracted_date = ref_date
                # .. century
                elif _resolution == DateTimeResolution.CENTURY:
                    if not is_relative_past:
                        _, extracted_date = get_century_range(ref_date)
                    else:
                        extracted_date = ref_date
                # .. millennium
                elif _resolution == DateTimeResolution.MILLENNIUM:
                    if not is_relative_past:
                        _, extracted_date = get_millennium_range(ref_date)
                    else:
                        extracted_date = ref_date
                elif _anchor_date:
                    extracted_date = ref_date
                
                # correction for one day shift
                # gets applied if no duration was extracted before
                #                       (resolution)
                #                            |
                # ie "remind me after X" -> day after X
                # while "3 days after X" -> X + 3 days
                if is_relative_past:
                    _offset = _offset or timedelta(days=-1)
                elif not _offset:
                    extracted_date = next_resolution(extracted_date, resolution)
            
            if extracted_date or _offset:
                date_found = True
                extracted_date = extracted_date or ref_date
                extracted_date += _offset
                relative_tok.isConsumed = True
                # TODO isDate/isTime?               
                ref_date = _anchor_date or ref_date

        # iterate the word list to extract a date
        if not date_found:
            current_date = now_local()
            final_date = False

            if named_date:
                date_found = True
                ref_date = datetime.combine(named_date.value,
                                            datetime.min.time()).replace(tzinfo=ref_date.tzinfo)
            if named_era:
                date_found = True
                ref_date = datetime.combine(named_era.value,
                                            datetime.min.time()).replace(tzinfo=ref_date.tzinfo)
            
            extracted_date: Optional[datetime] = None

            for token in date_words:
                if final_date:
                    break  # no more date updates allowed

                if token.isConsumed or token.isSymbolic:
                    continue

                # empty Token if oob
                tokPrevPrev = date_words[token.index - 2]
                tokPrev = date_words[token.index - 1]
                tokNext = date_words[token.index + 1]
                tokNextNext = date_words[token.index + 2]
                tokNextNextNext = date_words[token.index + 3]
                # Tokens for a near range check
                nearTok = date_words[token.index-3:token.index+3]

                _extracted_date: Optional[datetime] = None

                # TODO: lookahead for year?
                # we don't catch "next year", "last year" w/o "of".

                # parse preformatted dates
                # parse {DD.MM.YYYY}/{DD-MM-YYYY}/{MM/DD/YYYY}/{DD.MM.YY}/{DD.MM.}
                din5008 = list(
                    filter(lambda char: token.word.count(char) == 2, "./-"))
                if din5008:
                    _date = token.word.split(din5008[0])
                    # correction w/o year (11.12.)
                    if len(_date) == 3 and not _date[2]:
                        _date[2] = str(ref_date.year)
                    # correction 2 digit year (11.12.21) 
                    elif len(_date) == 3 and _date[2].isdigit() and len(_date[2]) == 2 \
                            and len(_date[0]) != 4:
                        ref_century = (ref_date.year // 100) * 100
                        ref_decade = int(str(ref_date.year)[-2:])
                        if ref_decade < 50:
                            _date[2] = str(ref_century + int(_date[2]))
                        else:
                            # year belongs to last century
                            _date[2] = str(ref_century - 100 + int(_date[2]))
                    if len(_date) == 3 and all([(len(d) == 4 or (0 < len(d) <= 2))
                                            and d.isnumeric() for d in _date]):
                        if len(_date[0]) != 4:
                            _date.reverse()
                        _date = list(map(int, _date))
                        # disambiguate to the best of our ability
                        if "/" in token.word or _date[1] > 12:
                            _date[1], _date[2] = _date[2], _date[1]
                        try:
                            extracted_date = datetime(*_date)
                            date_found = True
                            date_words.consume(token)
                        except ValueError:
                            pass
                        else:
                            final_date = True

                # parse "jetzt"/"heute"/"gestern"/"vorgestern"/"morgen"/"übermorgen"
                if token.lowercase in near_dates:
                    if token.lowercase == "morgen" and tokPrev.lowercase == "am":
                        continue
                    _offset = timedelta(days=near_dates[token.lowercase])
                    extracted_date = (ref_date or current_date) + _offset
                    if not time_found or not date_found:
                        extracted_date = extracted_date.replace(hour=0, minute=0, second=0)
                    date_found = True
                    date_words.consume(token)
                
                # parse {wochentag}
                elif token.lowercase.rstrip("s") in self._STRING_WEEKDAY:
                    date_found = True
                    int_week = self._STRING_WEEKDAY[token.lowercase.rstrip("s")]
                    _offset = self._STRING_WEEKDAY[token.lowercase.rstrip("s")] - \
                                ref_date.weekday()
                    # parse letzten {wochentag}
                    if tokPrev.lowercase in last:
                        if _offset >= 0:
                            _offset -= 7
                        extracted_date = ref_date + timedelta(days=_offset)
                        date_words.consume(tokPrev)
                    # 1./2./3./4. {wochentag} (ohne zusätzliche Angabe)
                    # NOTE: "1. Freitag IM ..." -> of_tok case
                    elif tokPrev.isOrdinal:
                        extracted_date = \
                            get_date_ordinal(tokPrev.number,
                                             offset=int_week,
                                             ref_date=ref_date,
                                             resolution=DateTimeResolution.DAY_OF_MONTH)
                        date_words.consume(tokPrev)
                    # kommenden/diesen/nächsten {wochentag}
                    else:
                        if _offset < -3:
                            _offset += 7
                        extracted_date = ref_date + timedelta(days=_offset)

                        if tokPrev.lowercase in this:
                            date_words.consume(tokPrev)
                        elif tokPrev.lowercase in future_markers:
                            date_words.consume(tokPrev)
                            # wochenüberschreitend kann man davon ausgehen,
                            # # das der wochentag der nächsten woche gemeint ist
                            # if int_week > _wd:
                            if _offset < 0:
                                extracted_date = extracted_date + timedelta(days=7)                            

                    assert extracted_date.weekday() == self._STRING_WEEKDAY[token.lowercase.rstrip("s")]
                    date_words.consume(token)
                
                # parse {monat}
                elif token.lowercase in self._STRING_MONTH:
                    date_found = True
                    _year = None
                    _int_month = self._STRING_MONTH[token.lowercase]
                    _extracted_date = ref_date.replace(month=_int_month, day=1)

                    # parse {monat} {YYYY}/{YY}
                    if tokNext.isDigit and \
                            resolution == DateTimeResolution.BEFORE_PRESENT:
                        _year = get_date_ordinal(tokNext.number,
                                                    ref_date=_extracted_date,
                                                    resolution=DateTimeResolution.BEFORE_PRESENT_YEAR).year
                        _extracted_date = _extracted_date.replace(year=_year)
                        date_words.consume(tokNext)
                    elif tokNext.isDigit:
                        if len(tokNext.word) == 2:
                            if tokNext.number <= 50:
                                _year = 2000 + tokNext.number
                            else:
                                _year = 1900 + tokNext.number
                        else:
                            _year = tokNext.number
                        _extracted_date = _extracted_date.replace(year=_year)
                        date_words.consume(tokNext)

                    if tokPrev.lowercase in last:
                        if _int_month > ref_date.month:
                            _extracted_date = _extracted_date.replace(
                                year=ref_date.year - 1)
                        date_words.consume(tokPrev)
                    elif tokPrev.lowercase in future_markers:
                        if _int_month < ref_date.month:
                            _extracted_date = _extracted_date.replace(
                                year=ref_date.year + 1)
                        date_words.consume(tokPrev)
                    # parse {1./1/...} {monat}
                    elif (tokPrev.isOrdinal or tokPrev.isDigit) and \
                            0 < tokPrev.number <= 31:
                        _extracted_date = _extracted_date.replace(
                            day=tokPrev.number
                        )
                        date_words.consume(tokPrev)
                        if _year:
                            final_date = True
                    
                    # parse begin/mitte/ende {monat}
                    _bme = nearTok.find(begin + mid + end)
                    if _bme:
                        _begin, _end = get_month_range(_extracted_date)
                        _mid = _begin + (_end - _begin) / 2
                        if _bme.lowercase in mid:
                            _extracted_date = _mid
                        elif _bme.lowercase in end:
                            _extracted_date = _end
                        date_words.consume(_bme)
                    
                    if extracted_date:
                        extracted_date = \
                            extracted_date.replace(month=_extracted_date.month,
                                                   day=_extracted_date.day)
                        if _year:
                            extracted_date = extracted_date.replace(year=_year)
                    else:
                        extracted_date = _extracted_date

                    date_words.consume(token)

                # parse ""... saison"
                # TODO: .. and not extracted_date
                elif token.lowercase in season_literal \
                        and not extracted_date:
                    _start, _end = get_season_range(ref_date,
                                                    hemisphere=hemisphere)
                    _ref_date = ref_date
                    if tokPrev.lowercase in last:
                        _ref_date = _start - timedelta(days=1)
                    elif tokPrev.lowercase in future_markers:
                        _ref_date = _end + timedelta(days=1)
                    elif tokPrev.isOrdinal:
                        # TODO
                        pass

                    if _ref_date != ref_date:
                        _start, _end = get_season_range(ref_date,
                                                        hemisphere=hemisphere)
                    extracted_date = _start
                    _bme = nearTok.find(begin + mid + end)
                    if _bme:
                        _mid = _start + (_end - _begin) / 2
                        if _bme.word in mid:
                            extracted_date = _mid
                        elif _bme.word in end:
                            extracted_date = _end
                        date_words.consume(_bme)
                    date_words.consume(token)
                
                # parse " ... frühling/sommer/herbst/winter ..."
                elif token.lowercase in season_markers \
                        and not extracted_date:
                
                    date_found = True
                    _season = self._SEASONS[token.lowercase.rstrip("s")]
                    _year = ref_date.year
                    if ((ref_date.month < 3) or \
                            (ref_date.month == 3 and ref_date.day < 20)) and \
                            ref_date.year == now_local().year:
                        if _season == Season.WINTER and \
                                hemisphere == Hemisphere.NORTH:
                            _year = ref_date.year - 1
                        elif _season == Season.SUMMER and \
                                hemisphere == Hemisphere.SOUTH:
                            _year = ref_date.year - 1
                    
                    # parse {season} {YYYY}/{YY}
                    if tokNext.isDigit and 1 < len(tokNext.word) <= 4:
                        if len(tokNext.word) == 2:
                            if tokNext.number <= 50:
                                _year = 2000 + tokNext.number
                            else:
                                _year = 1900 + tokNext.number
                        else:
                            _year = tokNext.number
                        extracted_date = season_to_date(_season,
                                                        _year,
                                                        ref_date.tzinfo,
                                                        hemisphere)
                        date_words.consume(tokNext)
                    # parse "letzten .."
                    elif tokPrev.lowercase in last:
                        extracted_date = last_season_date(_season,
                                                          ref_date,
                                                          hemisphere)
                        date_words.consume(tokPrev)
                    # parse "nächsten .."
                    elif tokPrev.lowercase in future_markers:
                        extracted_date = next_season_date(_season,
                                                          ref_date,
                                                          hemisphere)
                        date_words.consume(tokPrev)

                    else:
                        # parse "diesen .."
                        extracted_date = season_to_date(_season,
                                                        _year,
                                                        ref_date.tzinfo,
                                                        hemisphere)
                        if tokPrev.lowercase in this:
                            date_words.consume(tokPrev)
                    
                    # parse begin/mitte/ende ...
                    _bme = nearTok.find(begin + mid + end)
                    if _bme:
                        _start, _end = get_season_range(extracted_date,
                                                        hemisphere=hemisphere)
                        _mid = _start + (_end - _start) / 2
                        if _bme.lowercase in mid:
                            extracted_date = _mid
                        elif _bme.lowercase in end:
                            extracted_date = _end
                        date_words.consume(_bme)
                    
                    # astronomical dates are date and time
                    if extracted_date and extracted_date.hour != 0:
                        token.isDate = True
                        token.isTime = True
                    date_words.consume(token)

                # parse ".. tag .."
                elif token.lowercase in day_literal:
                    # parse {ORDINAL} day
                    if tokPrev.isOrdinal:
                        date_found = True
                        if resolution == DateTimeResolution.BEFORE_PRESENT:
                            extracted_date = get_date_ordinal(
                                tokPrev.number, ref_date=ref_date,
                                resolution=DateTimeResolution.BEFORE_PRESENT_DAY)
                        else:
                            extracted_date = ref_date.replace(
                                day=tokPrev.number)
                        date_words.consume(tokPrev)
                    # parse tag {NUMBER}
                    elif tokNext.isDigit:
                        date_found = True
                        extracted_date = ref_date.replace(day=tokNext.number)
                        date_words.consume(tokNext)
                    # parse "diesem tag"
                    elif tokPrev.lowercase in this:
                        date_found = True
                        extracted_date = ref_date
                        date_words.consume(tokPrev)
                    # parse "letzten tag"
                    elif tokPrev.lowercase in last:
                        date_found = True
                        extracted_date = ref_date - timedelta(days=1)
                        date_words.consume(tokPrev)
                    # parse "nächsten tag"
                    elif tokPrev.lowercase in future_markers:
                        date_found = True
                        extracted_date = ref_date + timedelta(days=1)
                        date_words.consume(tokPrev)

                    if extracted_date:
                        date_words.consume(token)
                        ref_date = extracted_date
                
                # parse ".. wochenende .."
                elif token.lowercase in weekend_literal:
                    _is_weekend = ref_date.weekday() >= 5
                    _resolution = DateTimeResolution.WEEKEND_OF_MONTH
                    # parse {ORDINAL} wochenende
                    if tokNext.isDigit:
                        ref_date = ref_date.replace(year=tokNext.number)
                        _resolution = DateTimeResolution.WEEKEND_OF_YEAR
                    if tokPrev.isOrdinal:
                        date_found = True
                        date_words.consume(tokPrev)
                        if resolution == DateTimeResolution.BEFORE_PRESENT:
                            extracted_date = get_date_ordinal(
                                tokPrev.number,
                                ref_date=ref_date,
                                resolution=DateTimeResolution.BEFORE_PRESENT_WEEKEND)
                        else:
                            # NOTE: 3. wochenende IM ... wird in of_tok case behandelt
                            extracted_date = get_date_ordinal(
                                tokPrev.number,
                                ref_date=ref_date,
                                resolution=_resolution)
                    # parse "dieses wochenende"
                    # TODO .. am wochenende
                    elif tokPrev.lowercase in this:
                        date_found = True
                        extracted_date, _end = get_weekend_range(ref_date)
                        date_words.consume(tokPrev)
                    # parse "nächstes wochenende"
                    elif tokPrev.lowercase in future_markers:
                        date_found = True
                        if not _is_weekend:
                            extracted_date, _end = get_weekend_range(ref_date)
                        else:
                            extracted_date, _end = get_weekend_range(ref_date +
                                                                     timedelta(
                                                                     weeks=1))
                        date_words.consume(tokPrev)
                    # parse "letztes wochenende"
                    elif tokPrev.lowercase in last:
                        date_found = True
                        extracted_date, _end = get_weekend_range(ref_date -
                                                                 timedelta(
                                                                 weeks=1))
                        date_words.consume(tokPrev)
                    date_words.consume(token)
                
                # parse "... woche ..."
                elif token.lowercase in week_literal:
                    # parse {ORDINAL} woche
                    if tokPrev.isOrdinal and 0 < tokPrev.number <= 53:
                        date_found = True
                        if resolution == DateTimeResolution.BEFORE_PRESENT:
                            _week = get_date_ordinal(
                                tokPrev.number,
                                resolution=DateTimeResolution.BEFORE_PRESENT_WEEK)
                        else:
                            _week = get_date_ordinal(
                                tokPrev.number,
                                ref_date=ref_date,
                                resolution=DateTimeResolution.WEEK_OF_YEAR)
                        extracted_date, _end = get_week_range(_week)
                        date_words.consume(tokPrev)
                    # parse "diese woche"
                    if tokPrev.lowercase in this:
                        date_found = True
                        extracted_date, _end = get_week_range(ref_date)
                        date_words.consume(tokPrev)
                    # parse "letzte woche"
                    elif tokPrev.lowercase in last:
                        date_found = True
                        _last_week = ref_date - timedelta(weeks=1)
                        extracted_date, _end = get_week_range(_last_week)
                        date_words.consume(tokPrev)
                    # parse "nächste woche"
                    elif tokPrev.lowercase in future_markers:
                        date_found = True
                        _last_week = ref_date + timedelta(weeks=1)
                        extracted_date, _end = get_week_range(_last_week)
                        date_words.consume(tokPrev)
                    # parse woche {NUMBER}
                    elif tokNext.isDigit and 0 < tokNext.number <= 53:
                        date_found = True
                        extracted_date = get_date_ordinal(
                            tokNext.number,
                            ref_date=ref_date,
                            resolution=DateTimeResolution.WEEK_OF_YEAR)
                        date_words.consume(tokNext)
                    # TODO: mitte der woche
                    # parse specific weekday (wochentag, anfang, mitte, ende)
                    _wd = nearTok.find(weekday_literals)
                    _bme = nearTok.find(begin + mid + end)
                    if _wd:
                        _wd_int = self._STRING_WEEKDAY[_wd.lowercase.rstrip('s')]
                        extracted_date += timedelta(days=_wd_int)
                        date_words.consume(_wd)
                    elif _bme:
                        _begin, _end = get_week_range(extracted_date)
                        _mid = _begin + (_end - _begin) / 2
                        if _bme.lowercase in mid:
                            extracted_date = _mid
                        elif _bme.lowercase in end:
                            extracted_date = _end
                        date_words.consume(_bme)
                    date_words.consume(token)
                
                # parse "... monat ..."
                elif token.lowercase in month_literal:
                    # parse {ORDINAL} monat
                    if tokPrev.isOrdinal and 0 < tokPrev.number <= 12:
                        date_found = True
                        if resolution == DateTimeResolution.BEFORE_PRESENT:
                            extracted_date = get_date_ordinal(
                                tokPrev.number,
                                resolution=DateTimeResolution.BEFORE_PRESENT_MONTH)
                        else:
                            extracted_date = get_date_ordinal(
                                tokPrev.number, ref_date=ref_date,
                                resolution=DateTimeResolution.MONTH_OF_YEAR)
                        date_words.consume(tokPrev)
                    # parse monat {NUMBER}
                    elif tokNext.isDigit and 0 < tokNext.number <= 12:
                        date_found = True
                        extracted_date = get_date_ordinal(
                            tokNext.number, ref_date=ref_date,
                            resolution=DateTimeResolution.MONTH_OF_YEAR)
                        date_words.consume(tokNext)
                    # parse "nächsten monat"
                    elif tokPrev.lowercase in future_markers:
                        date_found = True
                        _next_month = ref_date + timedelta(days=DAYS_IN_1_MONTH)
                        extracted_date = _next_month.replace(day=1)
                        date_words.consume(tokPrev)
                    # parse "letzen monat"
                    elif tokPrev.lowercase in last:
                        date_found = True
                        _last_month = ref_date - timedelta(days=DAYS_IN_1_MONTH)
                        extracted_date = _last_month.replace(day=1)
                        date_words.consume(tokPrev)
                    # parse "diesen monat"
                    else:
                        date_found = True
                        extracted_date = ref_date.replace(day=1)
                        if tokPrev.lowercase in this:
                            date_words.consume(tokPrev)

                    _bme = nearTok.find(begin + mid + end)
                    if _bme:
                        _begin, _end = get_month_range(extracted_date)
                        _mid = _begin + (_end - _begin) / 2
                        if _bme.lowercase in mid:
                            extracted_date = _mid
                        elif _bme.lowercase in end:
                            extracted_date = _end
                        date_words.consume(_bme)
                    date_words.consume(token)
                
                # parse ".. jahr"
                elif token.lowercase in year_literal:
                    # parse "dieses jahr"
                    date_found = True
                    if tokPrev.word in this:
                        _extracted_date = get_date_ordinal(
                            ref_date.year,
                            resolution=DateTimeResolution.YEAR)
                        date_words.consume(tokPrev)
                    # parse "letztes jahr"
                    elif tokPrev.lowercase in last:
                        _extracted_date = get_date_ordinal(
                            ref_date.year - 1,
                            resolution=DateTimeResolution.YEAR)
                        date_words.consume(tokPrev)
                    # parse "nächstes jahr"
                    elif tokPrev.lowercase in future_markers:
                        _extracted_date = get_date_ordinal(
                            ref_date.year + 1,
                            resolution=DateTimeResolution.YEAR)
                        date_words.consume(tokPrev)
                    # parse 1. jahr
                    elif tokPrev.isOrdinal:
                        if resolution == DateTimeResolution.BEFORE_PRESENT:
                            _extracted_date = get_date_ordinal(
                                tokPrev.number,
                                resolution=DateTimeResolution.BEFORE_PRESENT_YEAR)
                        else:
                            _extracted_date = get_date_ordinal(
                                tokPrev.number - 1,
                                resolution=DateTimeResolution.YEAR)
                        date_words.consume(tokPrev)
                    # parse jahr {NUMBER}
                    elif tokNext.isDigit:
                        _extracted_date = get_date_ordinal(
                            tokNext.number,
                            resolution=DateTimeResolution.YEAR)
                        date_words.consume(tokNext)
                    else:
                        _extracted_date = ref_date.replace(day=1, month=1)

                    _bme = nearTok.find(begin + mid + end)
                    if _bme:
                        _begin, _end = get_year_range(extracted_date)
                        _mid = _begin + (_end - _begin) / 2
                        if _bme.lowercase in mid:
                            _extracted_date = _mid
                        elif _bme.lowercase in end:
                            _extracted_date = _end
                        date_words.consume(_bme)
                    
                    if extracted_date:
                        extracted_date = \
                            extracted_date.replace(year=_extracted_date.year)
                    else:
                        extracted_date = _extracted_date
                    date_words.consume(token)
                
                # parse "dekade"
                elif token.lowercase in decade_literal:
                    _decade = (ref_date.year // 10) + 1
                    # parse "diese decade"
                    if tokPrev.lowercase in this:
                        date_found = True
                        extracted_date = get_date_ordinal(
                            _decade,
                            resolution=DateTimeResolution.DECADE)
                        date_words.consume(tokPrev)
                    # parse "letzte decade"
                    elif tokPrev.lowercase in last:
                        date_found = True
                        extracted_date = get_date_ordinal(
                            _decade - 1,
                            resolution=DateTimeResolution.DECADE)
                        date_words.consume(tokPrev)
                    # parse "nächste decade"
                    elif tokPrev.lowercase in future_markers:
                        date_found = True
                        extracted_date = get_date_ordinal(
                            _decade + 1,
                            resolution=DateTimeResolution.DECADE)
                        date_words.consume(tokPrev)
                    # parse 1. dekade
                    elif tokPrev.isOrdinal:
                        date_found = True
                        if resolution == DateTimeResolution.BEFORE_PRESENT:
                            extracted_date = get_date_ordinal(
                                tokPrev.number,
                                resolution=DateTimeResolution.BEFORE_PRESENT_DECADE)
                        else:
                            extracted_date = get_date_ordinal(
                                tokPrev.number,
                                resolution=DateTimeResolution.DECADE)
                        date_words.consume(tokPrev)
                    _bme = nearTok.find(begin + mid + end)
                    if _bme:
                        _begin, _end = get_decade_range(extracted_date)
                        _mid = _begin + (_end - _begin) / 2
                        if _bme.lowercase in mid:
                            extracted_date = _mid
                        elif _bme.lowercase in end:
                            extracted_date = _end
                        date_words.consume(_bme)
                    date_words.consume(token)
                
                # parse "millennium"
                elif token.lowercase in millennium_literal:
                    _mil = (ref_date.year // 1000) + 1
                    # parse "dieses millennium"
                    if tokPrev.lowercase in this:
                        date_found = True
                        extracted_date = get_date_ordinal(
                            _mil, ref_date=ref_date,
                            resolution=DateTimeResolution.MILLENNIUM)
                        date_words.consume(tokPrev)
                    # parse "letztes millennium"
                    elif tokPrev.lowercase in last:
                        date_found = True
                        extracted_date = get_date_ordinal(
                            _mil - 1, ref_date=ref_date,
                            resolution=DateTimeResolution.MILLENNIUM)
                        date_words.consume(tokPrev)
                    # parse "nächstes millennium"
                    elif tokPrev.lowercase in future_markers:
                        date_found = True
                        extracted_date = get_date_ordinal(
                            _mil + 1, ref_date=ref_date,
                            resolution=DateTimeResolution.MILLENNIUM)
                        date_words.consume(tokPrev)
                    # parse 1. millennium
                    elif tokPrev.isOrdinal:
                        date_found = True
                        if resolution == DateTimeResolution.BEFORE_PRESENT:
                            extracted_date = get_date_ordinal(
                                tokPrev.number, ref_date=extracted_date,
                                resolution=DateTimeResolution.BEFORE_PRESENT_MILLENNIUM)
                        else:
                            extracted_date = get_date_ordinal(
                                tokPrev.number, ref_date=extracted_date,
                                resolution=DateTimeResolution.MILLENNIUM)
                        date_words.consume(tokPrev)
                    _bme = nearTok.find(begin + mid + end)
                    if _bme:
                        _begin, _end = get_millennium_range(extracted_date)
                        _mid = _begin + (_end - _begin) / 2
                        if _bme.lowercase in mid:
                            extracted_date = _mid
                        elif _bme.lowercase in end:
                            extracted_date = _end
                        date_words.consume(_bme)
                    date_words.consume(token)

                # parse ".. jahrhundert .."
                elif token.lowercase in century_literal:
                    _century = (ref_date.year // 100) + 1
                    # parse "dieses jahrhundert"
                    if tokPrev.lowercase in this:
                        date_found = True
                        extracted_date = get_date_ordinal(
                            _century, ref_date=ref_date,
                            resolution=DateTimeResolution.CENTURY)
                        date_words.consume(tokPrev)
                    # parse "letztes jahrhundert"
                    elif tokPrev.lowercase in last:
                        date_found = True
                        extracted_date = get_date_ordinal(
                            _century - 1, ref_date=ref_date,
                            resolution=DateTimeResolution.CENTURY)
                        date_words.consume(tokPrev)
                    # parse "nächstes jahrhundert"
                    elif tokPrev.lowercase in future_markers:
                        date_found = True
                        extracted_date = get_date_ordinal(
                            _century + 1, ref_date=ref_date,
                            resolution=DateTimeResolution.CENTURY)
                        date_words.consume(tokPrev)
                    # parse "1. jahrhundert"
                    elif tokPrev.isOrdinal:
                        date_found = True
                        if resolution == DateTimeResolution.BEFORE_PRESENT:
                            extracted_date = get_date_ordinal(
                                tokPrev.number, ref_date=extracted_date,
                                resolution=DateTimeResolution.BEFORE_PRESENT_CENTURY)
                        else:
                            extracted_date = get_date_ordinal(
                                tokPrev.number, ref_date=extracted_date,
                                resolution=DateTimeResolution.CENTURY)
                        date_words.consume(tokPrev)
                    _bme = nearTok.find(begin + mid + end)
                    if _bme:
                        _begin, _end = get_century_range(extracted_date)
                        _mid = _begin + (_end - _begin) / 2
                        if _bme.lowercase in mid:
                            extracted_date = _mid
                        elif _bme.lowercase in end:
                            extracted_date = _end
                        date_words.consume(_bme)
                    date_words.consume(token)

                # parse day/mont/year is NUMBER
                elif token.lowercase in set_qualifiers and tokNext.isDigit:
                    # _ordinal = int(wordNext)
                    if tokPrev.lowercase in dateunit_literals:
                        date_found = True
                        date_words.consume([tokPrev,token,tokNext])
                        if tokPrev.lowercase in day_literal:
                            extracted_date = get_date_ordinal(
                                tokNext.number, ref_date=extracted_date,
                                resolution=DateTimeResolution.DAY_OF_MONTH)    
                        elif tokPrev.lowercase in month_literal:
                            extracted_date = get_date_ordinal(
                                tokNext.number, ref_date=extracted_date,
                                resolution=DateTimeResolution.MONTH_OF_YEAR)
                        elif tokPrev.lowercase in year_literal:
                            extracted_date = get_date_ordinal(
                                tokNext.number, ref_date=extracted_date,
                                resolution=DateTimeResolution.YEAR)
                        elif tokPrev.lowercase in decade_literal:
                            extracted_date = get_date_ordinal(
                                tokNext.number, ref_date=extracted_date,
                                resolution=DateTimeResolution.DECADE)
                        elif tokPrev.lowercase in century_literal:
                            extracted_date = get_date_ordinal(
                                tokNext.number, ref_date=extracted_date,
                                resolution=DateTimeResolution.CENTURY)
                        elif tokPrev.lowercase in millennium_literal:
                            extracted_date = get_date_ordinal(
                                tokNext.number, ref_date=extracted_date,
                                resolution=DateTimeResolution.MILLENNIUM)
                
                # bellow we parse standalone numbers, this is the major source
                # of ambiguity, caution advised

                # parse am {ordinal}
                # insbesondere für nachgelagerte datumsangaben, "im Mai am 15."
                elif token.isOrdinal and tokPrev.lowercase in date_markers:
                    date_found = True
                    ref_date = ref_date.replace(day=token.number)
                    if extracted_date:
                        extracted_date = extracted_date.replace(
                            day=token.number)
                    else:
                        extracted_date = ref_date
                    date_words.consume([token, tokPrev])

                # NOTE this is the place to check for requested
                # DateTimeResolution, usually not requested by the user but
                # rather used in recursion inside this very same method

                # NOTE2: the checks for XX_literal above may also need to
                # account for DateTimeResolution when parsing {Ordinal} {unit},
                # bellow refers only to default/absolute units

                # parse {N} unix time
                elif token.isDigit and resolution == \
                        DateTimeResolution.UNIX:
                    date_found = True
                    extracted_date = get_date_ordinal(
                        token.number, ref_date=extracted_date,
                        resolution=DateTimeResolution.UNIX_SECOND)
                    token.isTime = True
                    token.isDate = True
                    final_date = True
                    date_words.consume(token)
                # parse {N} julian days (since 1 January 4713 BC)
                elif token.isNumeric and resolution == \
                        DateTimeResolution.JULIAN:
                    date_found = True
                    extracted_date = get_date_ordinal(
                        token.number, ref_date=extracted_date,
                        resolution=DateTimeResolution.JULIAN_DAY)
                    token.isDate = True
                    if not token.isDigit:
                        token.isTime = True
                    final_date = True
                    date_words.consume(token)
                # # parse {N} ratadie (days since 1/1/1)
                elif token.isDigit and resolution == \
                        DateTimeResolution.RATADIE:
                    date_found = True
                    extracted_date = get_date_ordinal(
                        token.number, ref_date=extracted_date,
                        resolution=DateTimeResolution.RATADIE_DAY)
                    final_date = True
                    date_words.consume(token)
                # parse {N} lilian days
                elif token.isDigit and resolution == \
                        DateTimeResolution.LILIAN:
                    date_found = True
                    extracted_date = get_date_ordinal(
                        token.number, ref_date=extracted_date,
                        resolution=DateTimeResolution.LILIAN_DAY)
                    final_date = True
                    date_words.consume(token)
                # parse {year} {era}
                # "1992 nach christus"
                elif named_era and token.isDigit and tokNext in named_era:
                    date_found = True
                    _year = ref_date.year + token.number - 1
                    extracted_date = ref_date.replace(year=_year)
                    date_words.consume(token)
                # parse "die {YYYY}er"
                elif token.word.endswith("er") and \
                        token.word.rstrip("er").isdigit():
                    date_found = True
                    _year = token.word.rstrip("er")
                    if len(_year) == 2:
                        ref_century = (ref_date.year // 100) * 100
                        ref_decade = int(str(ref_date.year)[-2:])
                        if ref_decade > int(_year):
                            # year belongs to current century
                            # 13 -> 2013
                            _year = ref_century + int(_year)
                        else:
                            # year belongs to last century
                            # 69 -> 1969
                            _year = ref_century - 100 + int(_year)
                    else:
                        _year = int(_year)
                    extracted_date = ref_date.replace(year=_year)
                    date_words.consume(token)
            
        if (date_found or (time_found and not date_only)):
            extracted_date = extracted_date or ref_date
            if not isinstance(extracted_date, datetime):
                    extracted_date = datetime.combine(extracted_date,
                                                      datetime.min.time())
            if not extracted_date.tzinfo:
                extracted_date = extracted_date.replace(tzinfo=ref_date.tzinfo)
            # TODO: this is going the easy route to tag date, should differentiate
            # in future iterations, furthermore (positional) markers shouldn't be tagged
            for token in date_words:
                if token.isConsumed and (not token.isDuration and not token.isTime):
                    token.isDate = True
            if time_found:
                extracted_date = extracted_date.replace(hour=_hour,
                                                        minute=_min,
                                                        second=0,
                                                        microsecond=0)
                if extracted_date.date() == now_local().date() and \
                        extracted_date.time() < now_local().time() and \
                        not date_words.find(same_day_marker):
                    extracted_date += timedelta(days=1)

            # apply global resolution
            # returns the first of the reference frame
            if resolution == DateTimeResolution.MINUTE:
                extracted_date = extracted_date.replace(second=0, microsecond=0)
            elif resolution == DateTimeResolution.HOUR:
                extracted_date = extracted_date.replace(minute=0, second=0, microsecond=0)
            elif resolution == DateTimeResolution.DAY:
                extracted_date = extracted_date.replace(hour=0, minute=0, second=0, microsecond=0)
            elif resolution == DateTimeResolution.WEEK:
                extracted_date, _ = get_week_range(extracted_date)
            elif resolution == DateTimeResolution.MONTH:
                extracted_date, _ = get_month_range(extracted_date)
            elif resolution == DateTimeResolution.YEAR:
                extracted_date, _ = get_year_range(extracted_date)
            elif resolution == DateTimeResolution.DECADE:
                extracted_date, _ = get_decade_range(extracted_date)
            elif resolution == DateTimeResolution.CENTURY:
                extracted_date, _ = get_century_range(extracted_date)
            elif resolution == DateTimeResolution.MILLENNIUM:
                extracted_date, _ = get_millennium_range(extracted_date)
            else:
                extracted_date = extracted_date.replace(microsecond=0)
            
            # backwards compatible: return the whole date_words
            # to extract the remaining strings call property `remaining_text`
            dt = ReplaceableDatetime(extracted_date,
                                     date_words.tokens)
            return dt
        return None

    def extract_durations(self, data: Union[Tokens, str],
                                resolution=DurationResolution.TIMEDELTA) \
        -> List[ReplaceableTimedelta]:

        if isinstance(data, str):
            tokens = Tokens(data, lang="de-de")
        else:
            tokens = data

        numbers = GermanNumberParser().extract_numbers(tokens)

        # Einzahl, Mehrzahl und Flexionen
        pattern = r"\b(?P<unit>{unit}[nes]?[sn]?\b)"

        si_units: Dict[str, Any] = {
            'microseconds': '[Mm]ikrosekunden',
            'milliseconds': '[Mm]illisekunden',
            'seconds': '[Ss]ekunden',
            'minutes': '[Mm]inuten',
            'hours': '[Ss]tunden',
            'days': '[Tt]age',
            'weeks': '[Ww]ochen'
            }
        durations = []

        for number in numbers:
            # if number.end_index == tokens.end_index:
            #     break

            next_token = tokens[number.start_index + 1]
            if not next_token:
                break

            test_str = next_token.word
            toks = []
            
            if resolution == DurationResolution.TIMEDELTA:
                time_units = deepcopy(si_units)
                all_units: Dict[str, Any] = invert_dict(time_units)
                # value: (the unit converted in, factor)
                all_units.update({'[Mm]onate': ('days', DAYS_IN_1_MONTH),
                                  '[Jj]ahre': ('days', DAYS_IN_1_YEAR),
                                  '[Dd]ekaden': ('days', 10*DAYS_IN_1_YEAR),
                                  '[Jj]ahrhunderte': ('days', 100*DAYS_IN_1_YEAR)})

                for (unit_de, unit_en) in all_units.items():
                    if isinstance(unit_en, tuple):
                        factor = unit_en[1]
                        unit_en = unit_en[0]
                    else:
                        factor = 1
                    
                    if isinstance(time_units[unit_en], str):
                        time_units[unit_en] = 0
                    if toks:
                        continue

                    if re.match(pattern.format(unit=unit_de[:-1]), test_str):
                        time_units[unit_en] = number.value * factor
                        toks = tokens[number.start_index:number.end_index+2]

                delta = timedelta(**time_units)

            elif resolution in [DurationResolution.RELATIVEDELTA,
                                DurationResolution.RELATIVEDELTA_APPROXIMATE,
                                DurationResolution.RELATIVEDELTA_FALLBACK,
                                DurationResolution.RELATIVEDELTA_STRICT]:
                
                time_units = deepcopy(si_units)
                time_units.pop('milliseconds')
                time_units.update({'months': '[Mm]onate',
                                   'years': '[Jj]ahre'})
                all_units = invert_dict(time_units)
                all_units.update({'[Mm]illisekunden': ('microseconds', 1000),
                                  '[Dd]ekaden': ('years', 10),
                                  '[Jj]ahrhunderte': ('years', 100)})

                for (unit_de, unit_en) in all_units.items():
                    if isinstance(unit_en, tuple):
                        factor = unit_en[1]
                        unit_en = unit_en[0]
                    else:
                        factor = 1
                    
                    if isinstance(time_units[unit_en], str):
                        time_units[unit_en] = 0
                    if toks:
                        continue

                    if re.match(pattern.format(unit=unit_de[:-1]), test_str):
                        time_units[unit_en] = number.value * factor
                        toks = tokens[number.start_index:number.end_index+2]
                
                # microsecond, month, year must be ints
                time_units["microseconds"] = int(time_units["microseconds"])
                if resolution == DurationResolution.RELATIVEDELTA_FALLBACK:
                    for unit in ["months", "years"]:
                        value = time_units[unit]
                        _leftover, _ = math.modf(value)
                        if _leftover != 0:
                            print("[WARNING] relativedelta requires {unit} to be an "
                                "integer".format(unit=unit))
                            # fallback to timedelta resolution / raw tokens text with no flags
                            return self.extract_durations(tokens,
                                                          DurationResolution.TIMEDELTA)
                        time_units[unit] = int(value)
                elif resolution == DurationResolution.RELATIVEDELTA_APPROXIMATE:
                    _leftover, year = math.modf(time_units["years"])
                    time_units["months"] += 12 * _leftover
                    time_units["years"] = int(year)
                    _leftover, month = math.modf(time_units["months"])
                    time_units["days"] += DAYS_IN_1_MONTH * _leftover
                    time_units["months"] = int(month)
                else:
                    for unit in ["months", "years"]:
                        value = time_units[unit]
                        _leftover, _ = math.modf(value)
                        if _leftover != 0:
                            raise ValueError("relativedelta requires {unit} to be an "
                                             "integer".format(unit=unit))
                        time_units[unit] = int(value)
                
                delta = relativedelta(**time_units)
            
            else:
                # recalculate time in microseconds
                microseconds = 0
                factors = {"[Mm]ikrosekunden": 1,
                           '[Mm]illisekunden': 1000,
                           '[Ss]ekunden': 1000*1000,
                           '[Mm]inuten': 1000*1000*60,
                           '[Ss]tunden': 1000*1000*60*60,
                           '[Tt]age': 1000*1000*60*60*24,
                           '[Ww]ochen': 1000*1000*60*60*24*7,
                           '[Mm]onate': 1000*1000*60*60*24*DAYS_IN_1_MONTH,
                           '[Jj]ahre': 1000*1000*60*60*24*DAYS_IN_1_YEAR,
                           '[Jj]ahrzehnte': 1000*1000*60*60*24*DAYS_IN_1_YEAR*10,
                           '[Jj]ahrhunderte': 1000*1000*60*60*24*DAYS_IN_1_YEAR*100
                        }

                for (unit_de, factor) in factors.items():
                    if re.match(pattern.format(unit=unit_de[:-1]), test_str):
                        microseconds = number.value * factor
                        toks = tokens[number.start_index:number.end_index+2]
                        break

                if resolution == DurationResolution.TOTAL_MICROSECONDS:
                    delta = microseconds
                elif resolution == DurationResolution.TOTAL_MILLISECONDS:
                    delta = microseconds / factors['[Mm]illisekunden']
                elif resolution == DurationResolution.TOTAL_SECONDS:
                    delta = microseconds / factors['[Ss]ekunden']
                elif resolution == DurationResolution.TOTAL_MINUTES:
                    delta = microseconds / factors['[Mm]inuten']
                elif resolution == DurationResolution.TOTAL_HOURS:
                    delta = microseconds / factors['[Ss]tunden']
                elif resolution == DurationResolution.TOTAL_DAYS:
                    delta = microseconds / factors['[Tt]age']
                elif resolution == DurationResolution.TOTAL_WEEKS:
                    delta = microseconds / factors['[Ww]ochen']
                elif resolution == DurationResolution.TOTAL_MONTHS:
                    delta = microseconds / factors['[Mm]onate']
                elif resolution == DurationResolution.TOTAL_YEARS:
                    delta = microseconds / factors['[Jj]ahre']
                elif resolution == DurationResolution.TOTAL_DECADES:
                    delta = microseconds / factors['[Dd]ekaden']
                elif resolution == DurationResolution.TOTAL_CENTURIES:
                    delta = microseconds / factors['[Jj]ahrhunderte']
                else:
                    raise ValueError
            
            if toks:
                for tok in toks:
                    tok.isDuration = True

                prev_dur = durations[-1] if len(durations) else None
                # prev_tok = None if number.start_index == 0 else tokens[number.start_index - 1]
                prev_tok = tokens[number.start_index - 1]
                if prev_dur and \
                        any((prev_dur.end_index == number.start_index - 1,
                             prev_dur.end_index == number.start_index - 2 and 
                             (prev_tok.word == "und" or prev_tok.isComma)
                            )):
                    delta = prev_dur.value + delta
                    toks  = tokens[prev_dur.start_index:number.end_index+3]
                    if isinstance(delta, (float, int)):
                        durations[-1] = ReplaceableNumber(delta, toks)
                    else:
                        durations[-1] = ReplaceableTimedelta(delta, toks)
                else:
                    durations.append(ReplaceableTimedelta(delta, toks)
                                     if not isinstance(delta, (float, int))
                                     else ReplaceableNumber(delta, toks))
    
        durations.sort(key=lambda n: n.start_index)
        return durations

    def _tag_durations(self, tokens: Tokens):
        """
        Tags durations in the tokens.
        """
        self.extract_durations(tokens)
    
    def extract_duration(self, data: Union[Tokens, str],
                         resolution=DurationResolution.TIMEDELTA) \
        -> Optional[ReplaceableTimedelta]:
        durations = self.extract_durations(data, resolution=resolution)
        if len(durations) == 0:
            return None
        return durations[0]

    def extract_hemisphere(self, data: Union[Tokens, str],
                                    markers: Optional[List[str]] = None,
                                    ner: Optional[callable] = None) \
            -> Optional[Hemisphere]:
            """
            Extracts the hemisphere from the text.
            """

            # TODO Best to return a Location object with the hemisphere

            if ner is None:
                try:
                    from simple_NER.annotators.locations import LocationNER

                    ner = LocationNER()
                except ImportError:
                    ner = None
                    print("Location extraction disabled")
                    print("Run pip install simple_NER>=0.4.1")

            markers = markers or ["in", "auf", "am"]

            hemisphere = None

            if isinstance(data, str):
                tokens = Tokens(data, self.lang)
            else:
                tokens = data

            # parse {date} at {location}
            for token in tokens:
                if token.word in markers:
                    # this is used to parse seasons, which depend on
                    # geographical location
                    # "i know what you did last summer",  "winter is coming"
                    # usually the default will be set automatically based on user
                    # location

                    # NOTE these words are kept in the utterance remainder
                    # they are helpers but not part of the date itself

                    following = tokens[token.index+1:]
                    # parse {date} at north hemisphere
                    if any(part in following.text for part in 
                           self._HEMISPHERES[Hemisphere.NORTH]):
                        hemisphere = Hemisphere.NORTH
                    # parse {date} at south hemisphere
                    elif any(part in following.text for part in
                             self._HEMISPHERES[Hemisphere.SOUTH]):
                        hemisphere = Hemisphere.SOUTH
                    # parse {date} at {country/city}
                    elif ner is not None:
                        # parse string for Country names
                        for r in ner.extract_entities(tokens[token.index+1].word):
                            if r.entity_type == "Country":
                                if r.data["latitude"] < 0:
                                    hemisphere = Hemisphere.SOUTH
                                else:
                                    hemisphere = Hemisphere.NORTH
                        else:
                            #  or Capital city names
                            for r in ner.extract_entities(tokens[token.index+1].word):
                                if r.entity_type == "Capital City":
                                    if r.data["hemisphere"].startswith("s"):
                                        hemisphere = Hemisphere.SOUTH
                                    else:
                                        hemisphere = Hemisphere.NORTH

            return hemisphere


def get_named_date(date_: date, location_code: Optional[str] = None):
    """
    Get the name of a date.
    :param date_: A date or datetime object.
    :param location_code: A location code.
    :return: The name of the date.
    """
    try:
        _dt = datetime.combine(date_, datetime.min.time())
    except TypeError:
        raise TypeError("must be a date object")
    
    named_dates = get_named_dates(location_code, _dt)
    date_dict = invert_dict(named_dates)

    name = date_dict.get(date_)
    # if name:
    #     translate
    return name


def get_named_dates(location_code: Optional[str] = None,
                    ref_date: Optional[datetime] = None,
                    additional_dates: Optional[Dict[str, date]] = None,
                    hemisphere: Optional[Hemisphere] = None) -> Dict[str, date]:
    """
    Get the named dates for a one year period since ref_date.

    :param location_code: A location code.
    :param ref_date: A reference date.
    :param additional_dates: Additional dates to add to the named dates.
    :return: A dictionary of named dates.
    """
    if ref_date is None:
        ref_date = now_local()

    hemisphere = hemisphere or get_active_hemisphere()

    # compute both years if ref_date is not 1/1/ and trim -> dict of upcoming events
    years = [ref_date.year]
    if ref_date.month != 1 or ref_date.day != 1:
        years.append(ref_date.year + 1)
    _end_date = ref_date + relativedelta(years=1, minutes=-1)

    named_dates = dict()

    # additional local dates
    # to expand this, we should allow self-defined dates (on the fly)
    if additional_dates is None:
        source = None
        if location_code == "us":
            source = EnglishTimeTagger()
        elif location_code == "de":
            source = GermanTimeTagger()
        
        if source:
            named_dates.update(source.get_named_dates_local(ref_date))
    else:
        named_dates.update(additional_dates)

    # NOTE: those are dates most common around the world
    # OR local celbration days also celebrated in other countries
    # lines are blurry between being strict local and being global

    # if those differ in a particular country, they can be overwritten
    # in `get_named_dates_local` in the language specific tagger
    # TODO: islamic/hindu/chinese/.. calendar dates

    for year in years:
        easter_sunday = easter(year)
        christmas_day = date(year, 12, 25)
        # world dates
        _dates = {
            "New Year's Day": date(year, 1, 1),
            "Epiphany": date(year, 1, 6),
            "Chinese New Year": (date(year, 2, 1) + timedelta(days=(11 - date(year, 2, 1).weekday()) % 7)),
            "Valentine's Day": date(year, 2, 14),
            "St. Patrick's Day": date(year, 3, 17),
            "Meteorological Spring": date(year, 3, 1),
            "Vernal Equinox": next_season_date(Season.SPRING,
                                               datetime(year, 1, 1, tzinfo=ref_date.tzinfo),
                                               hemisphere).date(),
            "April Fool's Day": date(year, 4, 1),
            "Palm Sunday": easter_sunday - timedelta(days=7),
            "Maundy Thursday": easter_sunday - timedelta(days=3),
            "Good Friday": easter_sunday - timedelta(days=2),
            "Holy Saturday": easter_sunday - timedelta(days=1),
            "Easter Sunday": easter_sunday,
            "Easter Monday": easter_sunday + timedelta(days=1),
            "Fat Tuesday": easter_sunday - timedelta(days=47),
            "Ash Wednesday": easter_sunday - timedelta(days=46),
            "Mother's Day": (date(year, 5, 1) + timedelta(weeks=1, days=6 - date(year, 5, 1).weekday())),
            "Ascension Day": easter_sunday + timedelta(days=39),
            "Pentecost": easter_sunday + timedelta(days=49),
            "Whit Monday": easter_sunday + timedelta(days=50),
            "Trinity Sunday": easter_sunday + timedelta(days=56),
            "Corpus Christi": easter_sunday + timedelta(days=60),
            "Meteorological Summer": date(year, 6, 1),
            "Summer Solstice": next_season_date(Season.SUMMER,
                                                datetime(year, 1, 1, tzinfo=ref_date.tzinfo),
                                                hemisphere).date(),
            "Peter and Paul": date(year, 6, 29),
            "Assumption of Mary": date(year, 8, 15),
            "Canada Day": date(year, 7, 1),
            "American Independence Day": date(year, 7, 4),
            "Bastille Day": date(year, 7, 14),
            "International Friendship Day": date(year, 7, 30),
            "International Youth Day": date(year, 8, 12),
            "International Day of Peace": date(year, 9, 21),
            "Meteorological Autumn": date(year, 9, 1),
            "Autumnal Equinox": next_season_date(Season.FALL,
                                                 datetime(year, 1, 1, tzinfo=ref_date.tzinfo),
                                                 hemisphere).date(),
            "German Unity Day": date(year, 10, 3),
            "Halloween": date(year, 10, 31),
            "All Saints' Day": date(year, 11, 1),
            "All Souls' Day": date(year, 11, 2),
            "Hanukkah": (date(year, 11, 1) + timedelta(days=(2 - date(year, 11, 1).weekday()) % 7)),
            "St. Nicholas Day": date(year, 12, 6),
            "1st Advent": christmas_day - timedelta(days=(christmas_day.weekday() + 22)),
            "2nd Advent": christmas_day - timedelta(days=(christmas_day.weekday() + 15)),
            "3rd Advent": christmas_day - timedelta(days=(christmas_day.weekday() + 8)),
            "4th Advent": christmas_day - timedelta(days=(christmas_day.weekday() + 1)),
            "Meteorological Winter": date(year, 12, 1),
            "Winter Solstice": next_season_date(Season.WINTER,
                                                datetime(year, 1, 1, tzinfo=ref_date.tzinfo),
                                                hemisphere).date(),
            "Christmas Eve": date(year, 12, 24),
            "Christmas Day": date(year, 12, 25),
            "Boxing Day": date(year, 12, 26),
            "Kwanzaa": date(year, 12, 26),
            "New Year's Eve": date(year, 12, 31),
            "World Women's Day": date(year, 3, 8),
            "World Health Day": date(year, 4, 7),
            "World Earth Day": date(year, 4, 22),
            "World Fair Trade Day": (date(year, 5, 1) + timedelta(weeks=1, days=6 - date(year, 5, 1).weekday())),
            "World No Tobacco Day": date(year, 5, 31),
            "World Children's Day": date(year, 6, 1),
            "World Oceans Day": date(year, 6, 8),
            "World Blood Donation Day": date(year, 6, 14),
            "World Population Day": date(year, 7, 11),
            "World Youth Skills Day": date(year, 7, 15),
            "World Hepatitis Day": date(year, 7, 28),
            "World Breastfeeding Week": (date(year, 8, 1) + timedelta(weeks=1, days=6 - date(year, 8, 1).weekday())),
            "World Humanitarian Day": date(year, 8, 19),
            "World Alzheimer's Day": date(year, 9, 21),
            "World Tourism Day": date(year, 9, 27),
            "World Vegetarian Day": date(year, 10, 1),
            "World Animal Day": date(year, 10, 4),
            "World Mental Health Day": date(year, 10, 10),
            "World Food Day": date(year, 10, 16),
            "World Osteoporosis Day": date(year, 10, 20),
            "World Television Day": date(year, 11, 21),
            "World AIDS Day": date(year, 12, 1),
            "World Soil Day": date(year, 12, 5),
            "World Human Rights Day": date(year, 12, 10)
        }

        # Location aware holidays (holiday package)
        # needs the secondary location code
        location_code = location_code or get_active_location_code()
        if "-" in location_code:
            location_code = location_code.split("-")[1]

        holidays = country_holidays(location_code.upper(),
                                    years=year)
        _dates.update(invert_dict(holidays))
        _sorted_dates = dict(sorted(_dates.items(), key=lambda x: x[1]))

        for name, date_ in _sorted_dates.items():
            if date_ >= ref_date.date() and date_ <= _end_date.date():
                named_dates[name] = date_
    
    return named_dates


if __name__ == "__main__":
    t = EnglishTimeTagger()
    print(t.extract_durations("remind me in a minute"))
    print(t.extract_durations("remind me in one hundred minutes"))
    print(t.extract_durations("remind me in 10 minutes 5 seconds"))
    print(t.extract_durations("remind me in 10 minutes and 5 seconds"))
    print(t.extract_durations("remind me in 10 seconds and 5 hours and 10 seconds"))
    # [ReplaceableTimedelta(0:01:00, ['1', 'minute'])]
    # [ReplaceableTimedelta(1:40:00, ['one', 'hundred', 'minutes'])]
    # [ReplaceableTimedelta(0:10:05, ['10', 'minutes', '5', 'seconds'])]
    # [ReplaceableTimedelta(0:10:05, ['10', 'minutes', 'and', '5', 'seconds'])]
    # [ReplaceableTimedelta(0:00:10, ['10', 'seconds']), ReplaceableTimedelta(5:00:10, ['5', 'hours', 'and', '10', 'seconds'])]
