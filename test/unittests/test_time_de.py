import unittest

from ovos_classifiers.heuristics.time import GermanTimeTagger, EnglishTimeTagger
from ovos_classifiers.heuristics.time_helpers import get_week_range, date_to_season, \
    get_weekend_range
from dateutil.relativedelta import relativedelta
from datetime import timedelta, datetime, date, time, timezone
from ovos_classifiers.heuristics.time_helpers import DurationResolution, \
    DateTimeResolution, Hemisphere, Season
from ovos_utils.time import DAYS_IN_1_MONTH, DAYS_IN_1_YEAR, now_local


class TestGerman(unittest.TestCase):
    def setUp(self):
        self.tagger = GermanTimeTagger()
        self.ref_date = datetime(2117, 2, 3, 12, 0)
        self.now = now_local()
        self.default_time = self.now.time()
    
    def _extract_duration(self, text,
                          expected_duration,
                          expected_tokens=None,
                          resolution=DurationResolution.TIMEDELTA,
                          almostEqual=False):
        duration = \
            self.tagger.extract_durations(text, resolution=resolution)
        if duration:
            duration = duration[0]
        
        if almostEqual:
            self.assertAlmostEqual(duration.value, expected_duration)
        else:
            self.assertEqual(duration.value, expected_duration)

        if expected_tokens:
            duration_tokens = [t.word for t in duration if t.isDuration]
            self.assertEqual(duration_tokens, expected_tokens)

    def test_extract_durations_de(self):
        # defaulting to DurationResolution.TIMEDELTA

        self._extract_duration("10 sekunden",
                               timedelta(seconds=10.0),
                               ["10", "sekunden"])

        self._extract_duration("5 minuten",
                               timedelta(minutes=5),
                               ["5", "minuten"])

        self._extract_duration("2 stunden",
                               timedelta(hours=2),
                               ["2", "stunden"])

        self._extract_duration("halbe stunde",
                               timedelta(minutes=30),
                               ["0.5", "stunde"])

        self._extract_duration("1/2 stunde",
                               timedelta(minutes=30),
                               ["0.5", "stunde"])

        self._extract_duration("drei tage",
                               timedelta(days=3),
                               ["3", "tage"])

        self._extract_duration("neun einhalb wochen",
                               timedelta(days=66, hours=12),
                               ["9.5", "wochen"])

        self._extract_duration("7.5 sekunden",
                               timedelta(seconds=7.5),
                               ["7.5", "sekunden"])

        self._extract_duration("neuneinhalb tage und 2 stunden",
                               timedelta(days=9, hours=14),
                               ["9.5", "tage", "2", "stunden"])

        self._extract_duration("starte timer für 30 minuten",
                               timedelta(minutes=30),
                               ["30", "minuten"])

        self._extract_duration("nach stunden gibt es neunzehn minuten pause",
                               timedelta(minutes=19),
                               ["19", "minuten"])

        self._extract_duration("weck mich in 3 wochen, 497 tage und 391.6 sekunden",
                               timedelta(days=518, seconds=391.6),
                               ["3", "wochen", "497", "tage", "391.6", "sekunden"])

        self._extract_duration("der film ist eineinhalb stunden lang",
                               timedelta(hours=1, minutes=30),
                               ["1.5", "stunden"])

        self._extract_duration("10-sekunden",
                               timedelta(seconds=10.0),
                               ["10", "sekunden"])

        self._extract_duration("5-minuten",
                               timedelta(minutes=5),
                               ["5", "minuten"])

        self._extract_duration("ein monat",
                               timedelta(days=DAYS_IN_1_MONTH),
                               ["1", "monat"])

        self._extract_duration("3 monate",
                               timedelta(days=DAYS_IN_1_MONTH * 3),
                               ["3", "monate"])

        self._extract_duration("3 jahre",
                               timedelta(days=DAYS_IN_1_YEAR * 3),
                               ["3", "jahre"])

        self._extract_duration("ein jahr",
                               timedelta(days=DAYS_IN_1_YEAR),
                               ["1", "jahr"])

        self._extract_duration("eine dekade",
                               timedelta(days=DAYS_IN_1_YEAR * 10),
                               ["1", "dekade"])

        self._extract_duration("5 dekaden",
                               timedelta(days=DAYS_IN_1_YEAR * 10 * 5),
                               ["5", "dekaden"])

        self._extract_duration("1 jahrhundert",
                               timedelta(days=DAYS_IN_1_YEAR * 100),
                               ["1", "jahrhundert"])

        self._extract_duration("5 jahrhunderte",
                               timedelta(days=DAYS_IN_1_YEAR * 100 * 5),
                               ["5", "jahrhunderte"])

    def test_extract_durations_relativedelta(self):

        self._extract_duration("ein monat", relativedelta(months=1),
                               resolution=DurationResolution.RELATIVEDELTA)

        self._extract_duration("3 monate", relativedelta(months=3),
                               resolution=DurationResolution.RELATIVEDELTA)

        self._extract_duration("3 jahre", relativedelta(years=3),
                               resolution=DurationResolution.RELATIVEDELTA)

        self._extract_duration("ein jahr", relativedelta(years=1),
                               resolution=DurationResolution.RELATIVEDELTA)

        self._extract_duration("eine dekade", relativedelta(years=10),
                               resolution=DurationResolution.RELATIVEDELTA)

        self._extract_duration("5 dekaden", relativedelta(years=10 * 5),
                               resolution=DurationResolution.RELATIVEDELTA)

        self._extract_duration("1 jahrhundert", relativedelta(years=10 * 10),
                               resolution=DurationResolution.RELATIVEDELTA)

        self._extract_duration("5 jahrhunderte", relativedelta(years=10*10*5),
                               resolution=DurationResolution.RELATIVEDELTA)
        
        self.assertRaises(ValueError, self.tagger.extract_durations, "1.3 monate",
                          resolution=DurationResolution.RELATIVEDELTA)
        self.assertRaises(ValueError, self.tagger.extract_durations, "1.3 monate",
                          resolution=DurationResolution.RELATIVEDELTA_STRICT)

        self._extract_duration("1.3 monate",
                               timedelta(days=1.3 * DAYS_IN_1_MONTH),
                               resolution=DurationResolution.RELATIVEDELTA_FALLBACK)

        self._extract_duration("1.3 monate",
                               relativedelta(months=1, days=9.126000000000001),
                               resolution=DurationResolution.RELATIVEDELTA_APPROXIMATE)

    def test_extract_durations_total_microseconds(self):

        self._extract_duration("0.01 mikrosekunden", 0.01,
                               resolution=DurationResolution.TOTAL_MICROSECONDS)

        self._extract_duration("5 millisekunden", 5*1000,
                               resolution=DurationResolution.TOTAL_MICROSECONDS)

        self._extract_duration("10 sekunden", 10*1000*1000,
                               resolution=DurationResolution.TOTAL_MICROSECONDS)

        self._extract_duration("5 minuten und 20 sekunden",
                               5*1000*1000*60+20*1000*1000,
                               resolution=DurationResolution.TOTAL_MICROSECONDS)

        self._extract_duration("2 stunden 10 minuten",
                               2*1000*1000*60*60 + 10*1000*1000*60,
                               resolution=DurationResolution.TOTAL_MICROSECONDS)

        self._extract_duration("2 tage",
                               2 * 1000 * 1000 * 60 * 60 * 24,
                               resolution=DurationResolution.TOTAL_MICROSECONDS)

        self._extract_duration("2 wochen",
                               2 * 1000 * 1000 * 60 * 60 * 24 * 7,
                               resolution=DurationResolution.TOTAL_MICROSECONDS)

    def test_extract_durations_total_milliseconds(self):

        self._extract_duration("0.01 mikrosekunden", 0.01/1000,
                               resolution=DurationResolution.TOTAL_MILLISECONDS)

        self._extract_duration("5 millisekunden", 5,
                               resolution=DurationResolution.TOTAL_MILLISECONDS)

        self._extract_duration("10 sekunden", 10 * 1000,
                               resolution=DurationResolution.TOTAL_MILLISECONDS)

        self._extract_duration("5 minuten und 20 sekunden",
                               5 * 1000 * 60 + 20 * 1000,
                               resolution=DurationResolution.TOTAL_MILLISECONDS)

        self._extract_duration("2 stunden 10 minuten",
                               2 * 1000 * 60 * 60 + 10 * 1000 * 60,
                               resolution=DurationResolution.TOTAL_MILLISECONDS)

        self._extract_duration("2 tage",
                               2 * 1000 * 60 * 60 * 24,
                               resolution=DurationResolution.TOTAL_MILLISECONDS)

        self._extract_duration("2 wochen",
                               2 * 1000 * 60 * 60 * 24 * 7,
                               resolution=DurationResolution.TOTAL_MILLISECONDS)

    def test_extract_durations_total_seconds(self):

        self._extract_duration("0.01 mikrosekunden", 0.01/1000/1000,
                               resolution=DurationResolution.TOTAL_SECONDS,
                               almostEqual=True)

        self._extract_duration("5 millisekunden", 5/1000,
                               resolution=DurationResolution.TOTAL_SECONDS)

        self._extract_duration("10 sekunden", 10,
                               resolution=DurationResolution.TOTAL_SECONDS)

        self._extract_duration("5 minuten und 20 sekunden", 5 * 60 + 20,
                               resolution=DurationResolution.TOTAL_SECONDS)

        self._extract_duration("2 stunden 10 minuten", 2 * 60 * 60 + 10 * 60,
                               resolution=DurationResolution.TOTAL_SECONDS)

        self._extract_duration("2 tage", 2 * 60 * 60 * 24,
                               resolution=DurationResolution.TOTAL_SECONDS)

        self._extract_duration("2 wochen", 2 * 60 * 60 * 24 * 7,
                               resolution=DurationResolution.TOTAL_SECONDS)

    def test_extract_durations_total_minutes(self):

        self._extract_duration("0.01 mikrosekunden", 0.01/1000/1000/60,
                               resolution=DurationResolution.TOTAL_MINUTES,
                               almostEqual=True)

        self._extract_duration("5 millisekunden", 5/1000/60,
                               resolution=DurationResolution.TOTAL_MINUTES,
                               almostEqual=True)

        self._extract_duration("10 sekunden", 10/60,
                               resolution=DurationResolution.TOTAL_MINUTES)

        self._extract_duration("5 minuten und 20 sekunden", 5 + 20 / 60,
                               resolution=DurationResolution.TOTAL_MINUTES)

        self._extract_duration("2 stunden 10 minuten", 2 * 60 + 10,
                               resolution=DurationResolution.TOTAL_MINUTES)

        self._extract_duration("2 tage", 2 * 60 * 24,
                               resolution=DurationResolution.TOTAL_MINUTES)

        self._extract_duration("2 wochen", 2 * 60 * 24 * 7,
                               resolution=DurationResolution.TOTAL_MINUTES)

    def test_extract_durations_total_hours(self):

        self._extract_duration("0.01 mikrosekunden", 0.01/1000/1000/60/60,
                               resolution=DurationResolution.TOTAL_HOURS,
                               almostEqual=True)

        self._extract_duration("5 millisekunden", 5/1000/60/60,
                               resolution=DurationResolution.TOTAL_HOURS,
                               almostEqual=True)

        self._extract_duration("10 sekunden", 10/60/60,
                               resolution=DurationResolution.TOTAL_HOURS,
                               almostEqual=True)

        self._extract_duration("5 minuten und 20 sekunden", 5 / 60 + 20 / 60 / 60,
                               resolution=DurationResolution.TOTAL_HOURS,
                               almostEqual=True)

        self._extract_duration("2 stunden 10 minuten", 2 + 10 / 60,
                               resolution=DurationResolution.TOTAL_HOURS,
                               almostEqual=True)

        self._extract_duration("2 tage", 2 * 24,
                               resolution=DurationResolution.TOTAL_HOURS)

        self._extract_duration("2 wochen", 2 * 24 * 7,
                               resolution=DurationResolution.TOTAL_HOURS)

    def test_extract_durations_total_days(self):

        self._extract_duration("0.01 mikrosekunden", 0.01/1000/1000/60/60/24,
                               resolution=DurationResolution.TOTAL_DAYS,
                               almostEqual=True)

        self._extract_duration("5 millisekunden", 5/1000/60/60/24,
                               resolution=DurationResolution.TOTAL_DAYS,
                               almostEqual=True)

        self._extract_duration("10 sekunden", 10/60/60/24,
                               resolution=DurationResolution.TOTAL_DAYS,
                               almostEqual=True)

        self._extract_duration("5 minuten und 20 sekunden",
                               5 / 60 / 24 + 20 / 60 / 60 / 24,
                               resolution=DurationResolution.TOTAL_DAYS,
                               almostEqual=True)

        self._extract_duration("2 stunden 10 minuten", 2 / 24 + 10 / 60 / 24,
                               resolution=DurationResolution.TOTAL_DAYS,
                               almostEqual=True)

        self._extract_duration("2 tage", 2,
                               resolution=DurationResolution.TOTAL_DAYS)

        self._extract_duration("2 wochen", 2 * 7,
                               resolution=DurationResolution.TOTAL_DAYS)

        self._extract_duration("2 monate", 2 * DAYS_IN_1_MONTH,
                               resolution=DurationResolution.TOTAL_DAYS)

        self._extract_duration("2 jahre", 2 * DAYS_IN_1_YEAR,
                               resolution=DurationResolution.TOTAL_DAYS)

        self._extract_duration("2 jahrzehnte", 2 * DAYS_IN_1_YEAR * 10,
                               resolution=DurationResolution.TOTAL_DAYS)

    def test_extract_durations_total_weeks(self):

        self._extract_duration("10 sekunden", 10/60/60/24/7,
                               resolution=DurationResolution.TOTAL_WEEKS,
                               almostEqual=True)

        self._extract_duration("5 minuten und 20 sekunden",
                               5 / 60 / 24 / 7 + 20 / 60 / 60 / 24 / 7,
                               resolution=DurationResolution.TOTAL_WEEKS,
                               almostEqual=True)

        self._extract_duration("2 stunden 10 minuten",
                               2 / 24 / 7 + 10 / 60 / 24 / 7,
                               resolution=DurationResolution.TOTAL_WEEKS,
                               almostEqual=True)

        self._extract_duration("2 tage", 2 / 7,
                               resolution=DurationResolution.TOTAL_WEEKS)

        self._extract_duration("2 wochen", 2,
                               resolution=DurationResolution.TOTAL_WEEKS)

        self._extract_duration("2 monate", 2 * DAYS_IN_1_MONTH / 7,
                               resolution=DurationResolution.TOTAL_WEEKS)

        self._extract_duration("2 jahre", 2 * DAYS_IN_1_YEAR / 7,
                               resolution=DurationResolution.TOTAL_WEEKS)

        self._extract_duration("2 jahrzehnte", 2 * DAYS_IN_1_YEAR * 10 / 7,
                    resolution=DurationResolution.TOTAL_WEEKS)

    def test_extract_durations_total_months(self):

        self._extract_duration("10 sekunden", 10/60/60/24/DAYS_IN_1_MONTH,
                               resolution=DurationResolution.TOTAL_MONTHS,
                               almostEqual=True)

        self._extract_duration("5 minuten und 20 sekunden",
                               5 / 60 / 24 / DAYS_IN_1_MONTH + 20 / 60 / 60 / 24 / DAYS_IN_1_MONTH,
                               resolution=DurationResolution.TOTAL_MONTHS,
                               almostEqual=True)

        self._extract_duration("2 stunden 10 minuten",
                               2 / 24 / DAYS_IN_1_MONTH + 10 / 60 / 24 / DAYS_IN_1_MONTH,
                               resolution=DurationResolution.TOTAL_MONTHS,
                               almostEqual=True)

        self._extract_duration("2 tage", 2 / DAYS_IN_1_MONTH,
                    resolution=DurationResolution.TOTAL_MONTHS)

        self._extract_duration("2 wochen", 2 * 7 / DAYS_IN_1_MONTH,
                               resolution=DurationResolution.TOTAL_MONTHS)

        self._extract_duration("2 monate", 2,
                               resolution=DurationResolution.TOTAL_MONTHS)

        self._extract_duration("2 jahre", 2 * DAYS_IN_1_YEAR / DAYS_IN_1_MONTH,
                               resolution=DurationResolution.TOTAL_MONTHS,
                               almostEqual=True)

        self._extract_duration("2 jahrzehnte", 2 * DAYS_IN_1_YEAR * 10 / DAYS_IN_1_MONTH,
                               resolution=DurationResolution.TOTAL_MONTHS,
                               almostEqual=True)

    def test_extract_durations_total_years(self):

        self._extract_duration("10 sekunden", 10/60/60/24/DAYS_IN_1_YEAR,
                               resolution=DurationResolution.TOTAL_YEARS,
                               almostEqual=True)

        self._extract_duration("5 minuten und 20 sekunden",
                               5 / 60 / 24 / DAYS_IN_1_YEAR + 20 / 60 / 60 / 24 / DAYS_IN_1_YEAR,
                               resolution=DurationResolution.TOTAL_YEARS,
                               almostEqual=True)

        self._extract_duration("2 stunden 10 minuten",
                               2 / 24 / DAYS_IN_1_YEAR + 10 / 60 / 24 / DAYS_IN_1_YEAR,
                               resolution=DurationResolution.TOTAL_YEARS,
                               almostEqual=True)

        self._extract_duration("2 tage", 2 / DAYS_IN_1_YEAR,
                               resolution=DurationResolution.TOTAL_YEARS)

        self._extract_duration("2 wochen", 2 * 7 / DAYS_IN_1_YEAR,
                               resolution=DurationResolution.TOTAL_YEARS)

        self._extract_duration("2 monate", 2 * DAYS_IN_1_MONTH / DAYS_IN_1_YEAR,
                               resolution=DurationResolution.TOTAL_YEARS)

        self._extract_duration("2 jahre", 2,
                               resolution=DurationResolution.TOTAL_YEARS,
                               almostEqual=True)

        self._extract_duration("2 jahrzehnte", 2 * 10,
                               resolution=DurationResolution.TOTAL_YEARS,
                               almostEqual=True)

        self._extract_duration("2 jahrhunderte", 2 * 100,
                               resolution=DurationResolution.TOTAL_YEARS,
                               almostEqual=True)
    
    def _extract_time(self, time_str,
                            expected_time,
                            expected_tokens=None,
                            resolution=DateTimeResolution.SECOND,
                            anchor=None,
                            hemi=Hemisphere.NORTH):

        anchor = anchor or self.ref_date
        extracted_time = self.tagger.extract_time(time_str,
                                                    anchor,
                                                    resolution,
                                                    hemisphere=hemi)
        if extracted_time is None:
            self.assertEqual(extracted_time, expected_time)
        else:
            self.assertEqual(extracted_time.value, expected_time)
        
        if expected_tokens:
            duration_tokens = [t.word for t in extracted_time if t.isTime]
            self.assertEqual(duration_tokens, expected_tokens)

    def test_extract_time(self):
        self._extract_time("Stelle Alarm um 9:00 Uhr",
                           time(9, 0, 0),
                           ["9:00", "Uhr"])
        self._extract_time("Stelle Alarm um 21:00 Uhr",
                           time(21, 0, 0),
                           ["21:00", "Uhr"])
        self._extract_time("Stelle Alarm um 9:00 AM",
                           time(9, 0, 0),
                           ["9:00", "AM"])
        self._extract_time("Stelle Alarm um 9:00 am",
                           time(9, 0, 0),
                           ["9:00", "am"])
        self._extract_time("Stelle Alarm um 9:00 pm",
                           time(21, 0, 0),
                           ["9:00", "pm"])
        self._extract_time("Stelle Alarm um 9:00 p.m.",
                           time(21, 0, 0),
                           ["9:00", "p.m."])
        self._extract_time("Stelle Alarm um 9:00 a.m.",
                           time(9, 0, 0),
                           ["9:00", "a.m."])
        # NOTE: This "time format" (eg. sent by whisper) is interpretated as float
        # number parser is correcting this issue
        self._extract_time("Stelle Alarm um 9.00 Uhr",
                           time(9, 0, 0),
                           ["9:00", "Uhr"])
        self._extract_time("Stelle Alarm um 9.00 PM",
                           time(21, 0, 0),
                           ["9:00", "PM"])
        self._extract_time("Stelle Alarm um 9 Uhr",
                           time(9, 0, 0),
                           ["9", "Uhr"])
        self._extract_time("Stelle Alarm um 9 Uhr 30",
                           time(9, 30, 0),
                           ["9", "Uhr", "30"])
        self._extract_time("weck mich um 10 vor acht",
                           time(7, 50, 0),
                           ["10", "vor", "8"])
        self._extract_time("weck mich um 10 nach acht",
                           time(8, 10, 0),
                           ["10", "nach", "8"])
        self._extract_time("weck mich um dreiviertel acht",
                           time(7, 45, 0),
                           ["7:45"])
        self._extract_time("weck mich um drei viertel acht",
                           time(7, 45, 0),
                           ["7:45"])
        self._extract_time("weck mich um drei viertel acht abends",
                           time(19, 45, 0),
                           ["7:45", "abends"])
        self._extract_time("weck mich um halb neun",
                           time(8, 30, 0),
                           ["8:30"])
        self._extract_time("weck mich nachts um halb neun",
                           time(20, 30, 0),
                           ["nachts", "8:30"])
        
        # tts failure
        self._extract_time("Stelle Alarm um 9 Uhr 30 Uhr",
                           time(9, 30, 0),
                           ["9", "Uhr", "30", "Uhr"])
        self._extract_time("Stelle Alarm um 9 30 am",
                           time(9, 30, 0),
                           ["9", "30", "am"])                               

    def test_extract_time_ambigiguous(self):
        self._extract_time("Stelle Alarm um 9 an wochenenden",
                           time(9, 0, 0),
                           ["9"])
        self._extract_time("um 8 heute abend",
                           time(20, 0, 0),
                           ["8", "abend"])
        # pm is split from the time during tokenization
        # ie not really a test for missing am/pm
        self._extract_time("um 8:30uhr heute abend",
                           time(20, 30, 0),
                           ["8:30", "uhr", "abend"])
        # Tests a time with ':' & without am/pm
        self._extract_time("Stelle Alarm abends um 9:30",
                           time(21, 30, 0),
                           ["abends", "9:30"])
        self._extract_time("Stelle Alarm nachts um drei Uhr zehn",
                           time(3, 10, 0),
                           ["nachts", "3", "Uhr", "10"])
        self._extract_time("Stelle Alarm um 9:00 nachts",
                           time(21, 0, 0),
                           ["9:00", "nachts"])
        # Check if it picks the intent irrespective of correctness
        self._extract_time("Stelle Alarm um 9 uhr nachts",
                           time(21, 0, 0),
                           ["9", "uhr", "nachts"])
        self._extract_time("Stelle Alarm um 9 30 a.m. abends",
                           time(21, 30, 0),
                           ["9", "30", "a.m.", "abends"])
        self._extract_time("Erinner mich an das Spiel heute nacht um 11:30",
                           time(23, 30, 0),
                           ["nacht", "11:30"])
        self._extract_time("Stelle Alarm um 7:30 an wochenenden",
                           time(7, 30, 0),
                           ["7:30"])
        self._extract_time("Stelle Alarm 9 30",
                           None)
    
    def test_extract_time_daytimes(self):
        self._extract_time("Stelle Alarm am Morgen",
                           time(6, 0, 0),
                           ["Morgen"])
        self._extract_time("Stelle Alarm am Vormittag",
                           time(9, 0, 0),
                           ["Vormittag"])
        # day shift if the `time` is in the past and not specifically mentioned
        # TODO: -> extract_datetime test
        # _dt = self.tagger.extract_date("set alarm in the morning").value
        # self.assertEqual(_dt.weekday(), self.now.weekday() + 1)
        self._extract_time("Stelle Alarm am Nachmittag",
                           time(15, 0, 0),
                           ["Nachmittag"])
        self._extract_time("Stelle Alarm nachmittags um 5",
                           time(17, 0, 0),
                           ["nachmittags", "5"])
        self._extract_time("Stelle Alarm um 3 Uhr 30 nachmittags",
                           time(15, 30, 0),
                           ["3", "Uhr", "30", "nachmittags"])
        self._extract_time("Stelle Alarm am abend",
                           time(18, 0, 0),
                           ["abend"])
        self._extract_time("Stelle nachts einen Alarm",
                           time(21, 0, 0),
                           ["nachts"])
        self._extract_time("Stelle mittags einen Alarm",
                           time(12, 0, 0),
                           ["mittags"])
        self._extract_time("Stelle Alarm um Mitternacht",
                           time(0, 0, 0),
                           ["Mitternacht"])
    
    def _extract_datetime(self,
                    time_str,
                    expected_time,
                    resolution=DateTimeResolution.SECOND,
                    anchor=None,
                    hemi=Hemisphere.NORTH):
        anchor = anchor or self.ref_date
        extracted_time = self.tagger.extract_datetime(time_str,
                                                      anchor,
                                                      resolution,
                                                      hemisphere=hemi)
        if extracted_time is None:
            self.assertEqual(extracted_time, expected_time)
        else:
            self.assertEqual(extracted_time.value.replace(tzinfo=None),
                             expected_time)


    def test_extract_datetime(self):
        self._extract_datetime("Ich werde am 15. Oktober 2022 um 14:30 Uhr eine Besprechung haben.",
                               datetime(2022, 10, 15, 14, 30))
        self._extract_datetime("Stell einen Countdown für Neujahr.",
                               datetime(2118, 1, 1, 0, 0))
    
    def test_extract_datetime_ambiguous(self):
        pass

    def test_extract_datetime_of(self):
        self._extract_datetime("Ich werde im Januar 2022 um 14:30 Uhr eine Besprechung haben.",
                               datetime(2022, 1, 1, 14, 30))
        # utc to not have to deal with configured timezones
        self._extract_datetime("Wir treffen uns im Sommer um 10:00 Uhr.",
                               datetime(2024, 6, 20, 10, 00),
                               anchor = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc))
        self._extract_datetime("Ich habe im letzten Jahr am dritten Mai um 15:00 Uhr geheiratet.",
                               datetime(2116, 5, 3, 15, 0))
        self._extract_datetime("Ich werde im nächsten Monat um 9:00 Uhr anfangen.",
                               datetime(2117, 3, 1, 9, 0))
        self._extract_datetime("Ich werde im nächsten Jahr um 12:00 Uhr Geburtstag haben.",
                               datetime(2118, 1, 1, 12, 0))
        self._extract_datetime("Wir haben im Neujahr um 12:00 Uhr eine Party.",
                               datetime(2118, 1, 1, 12, 0))
        self._extract_datetime("dritten Oktober im Jahr 2018 um 8:00 Uhr",
                               datetime(2018, 10, 3, 8, 0))
    
    def test_extract_datetime_day_of(self):
        self._extract_datetime("Erster Tag im Monat Mai um 8:00 Uhr",
                               datetime(2117, 5, 1, 8, 0))
        self._extract_datetime("Zweiter Tag in Woche 43 um 8:00 Uhr",
                               datetime(2117, 10, 26, 8, 0))
        self._extract_datetime("wir treffen uns am zehnten Tag im Mai um 8:00 Uhr",
                               datetime(2117, 5, 10, 8, 0))
        self._extract_datetime("wir treffen uns an Tag zehn im Mai um 8:00 Uhr",
                               datetime(2117, 5, 10, 8, 0))
        self._extract_datetime("Zweiter Tag im Mai 2018 um 8:00 Uhr",
                               datetime(2018, 5, 2, 8, 0))
        self._extract_datetime("wir treffen uns am letzten Tag im Mai um 8:00 Uhr",
                               datetime(2117, 5, 31, 8, 0))
        self._extract_datetime("letzter Tag im Jahr um 8:00 Uhr",
                               datetime(2117, 12, 31, 8, 0))
    
    def _extract_date(self,
                    time_str,
                    expected_date,
                    resolution=DateTimeResolution.DAY,
                    anchor=None,
                    hemi=Hemisphere.NORTH):
        anchor = anchor or self.ref_date
        extracted_date = self.tagger.extract_date(time_str,
                                                  anchor,
                                                  resolution,
                                                  hemisphere=hemi)
        if extracted_date is None:
            self.assertEqual(extracted_date, expected_date)
        else:
            self.assertEqual(extracted_date.value,
                             expected_date)

    def test_extract_date_preformatted(self):
        self._extract_date("11.12.2018",
                           date(2018, 12, 11))
        self._extract_date("1.12.2018",
                           date(2018, 12, 1))
        self._extract_date("11.1.2018",
                           date(2018, 1, 11))
        self._extract_date("1.1.2018",
                           date(2018, 1, 1))
        self._extract_date("11.12.18",
                           date(2118, 12, 11))
        self._extract_date("1.12.",
                           date(2117, 12, 1))
        self._extract_date("11/12/2018",
                           date(2018, 11, 12))
        self._extract_date("11-12-2018",
                           date(2018, 12, 11))
        self._extract_date("2018-12-11",
                           date(2018, 12, 11))
        # abnorm
        self._extract_date("11-21-2018",
                           date(2018, 11, 21))
        # no date
        self._extract_date("11-2d-1800",
                           None)
    
    def test_extract_date_neardates(self):
        self._extract_date("gestern",
                           date(2117, 2, 2))
        self._extract_date("heute",
                           date(2117, 2, 3))
        self._extract_date("morgen",
                           date(2117, 2, 4))
        self._extract_date("übermorgen",
                           date(2117, 2, 5))
        self._extract_date("vorgestern",
                           date(2117, 2, 1))

    def test_extract_date_day(self):
        self._extract_date("tag 1",
                           date(2117, 2, 1))
        self._extract_date("kommenden tag",
                           date(2117, 2, 4))
        self._extract_date("nächsten tag",
                           date(2117, 2, 4))
        self._extract_date("letzten tag",
                           date(2117, 2, 2))
    
    def test_extract_date_day_of(self):
        self._extract_date("am 1. Tag der Woche",
                           date(2117, 2, 1))
        self._extract_date("am 1. Tag im Mai",
                           date(2117, 5, 1))
        self._extract_date("am 1. Tag im Jahr",
                           date(2117, 1, 1))
        
    def test_extract_date_day_relative(self):
        self._extract_date("in zwei Tagen",
                           date(2117, 2, 5))
        self._extract_date("vor zwei Tagen",
                           date(2117, 2, 1))
        self._extract_date("zwei Tage vor dem 15.",
                           date(2117, 2, 13))
        self._extract_date("zwei Tage nach dem 15. Mai",
                           date(2117, 5, 17))
        self._extract_date("zwei Tage vor dem 15. Mai",
                           date(2117, 5, 13))

    def test_extract_date_weekday(self):
        self._extract_date("Ich hatte am Montag eine Besprechung.",
                           date(2117, 2, 1))
        self._extract_date("Ich hatte am Dienstag eine Besprechung.",
                           date(2117, 2, 2))
        self._extract_date("Ich werde am Mittwoch eine Besprechung haben.",
                           date(2117, 2, 3))
        self._extract_date("Ich werde am Donnerstag eine Besprechung haben.",
                           date(2117, 2, 4))
        self._extract_date("Ich werde am Freitag eine Besprechung haben.",
                           date(2117, 2, 5))
        self._extract_date("Ich werde am Samstag eine Besprechung haben.",
                           date(2117, 2, 6))
        self._extract_date("Ich werde am Sonntag eine Besprechung haben.",
                           date(2117, 2, 7))
        self._extract_date("Montag",
                           date(2117, 2, 1))
        self._extract_date("Montag nächster Woche",
                           date(2117, 2, 8))
        self._extract_date("nächsten Montag",
                           date(2117, 2, 8))
        self._extract_date("letzten Montag",
                           date(2117, 2, 1))
        
    def test_extract_date_weekday_of(self):
        self._extract_date("Erster Samstag im Jahr",
                           date(2117, 1, 2))
        self._extract_date("Erster Samstag im Juni 2023",
                           date(2023, 6, 3))
        self._extract_date("Samstag der ersten Woche im Juni 2023",
                           date(2023, 6, 10))
        self._extract_date("Samstag in der Woche 43",
                           date(2117, 10, 30))
        self._extract_date("Erster Samstag des Monats Mai 2023",
                           date(2023, 5, 6))
        self._extract_date("Erster Samstag im Jahr 2023",
                           date(2023, 1, 7))
    
    def test_extract_date_weekday_relative(self):
        self._extract_date("Montag vor einer Woche",
                           date(2117, 1, 25))
        self._extract_date("Montag in einer Woche",
                           date(2117, 2, 8))
    
    def test_extract_date_week(self):
        self._extract_date("in der zweiten Woche",
                           date(2117, 1, 11))
        self._extract_date("in der zweiten Woche im jahr",
                           date(2117, 1, 11))
        self._extract_date("in der zweiten Woche im jahr 2023",
                           date(2023, 1, 9))
        self._extract_date("in Woche zwei",
                           date(2117, 1, 11))
        self._extract_date("dreiundvierzigste Woche",
                           date(2117, 10, 25))        
        self._extract_date("in der nächsten Woche",
                           date(2117, 2, 8))
        self._extract_date("in der letzten Woche",
                           date(2117, 1, 25))
        self._extract_date("Anfang nächster Woche",
                           date(2117, 2, 8))
        self._extract_date("Mitte nächster Woche",
                           date(2117, 2, 11))
        self._extract_date("Ende nächster Woche",
                           date(2117, 2, 14))
        self._extract_date("nächste Woche samstags",
                           date(2117, 2, 13))
        self._extract_date("Samstag nächster Woche",
                           date(2117, 2, 13))
        self._extract_date("Anfang letzter Woche",
                           date(2117, 1, 25))
        self._extract_date("Mitte letzter Woche",
                           date(2117, 1, 28))
        self._extract_date("Ende letzter Woche",
                           date(2117, 1, 31))
        self._extract_date("in einer Woche",
                           date(2117, 2, 10))
        self._extract_date("vor einer Woche",
                           date(2117, 1, 27))
        
    def test_extract_date_week_of(self):
        self._extract_date("wir haben einen termin in der zweiten Woche im Mai 2023",
                           date(2023, 5, 8))
        self._extract_date("Erste Woche des Jahres 2023",
                           date(2023, 1, 2))
        self._extract_date("Erste Woche im Jahr",
                           date(2117, 1, 4))
        self._extract_date("in der ersten Woche des nächsten monats",
                           date(2117, 3, 1))
    
    def test_extract_date_month(self):
        self._extract_date("im Januar",
                           date(2117, 1, 1))
        self._extract_date("im Januar 2023",
                            date(2023, 1, 1))
        self._extract_date("im Januar 23",
                            date(2023, 1, 1))
        self._extract_date("im zweiten Monat",
                            date(2117, 2, 1))
        self._extract_date("im zweiten Monat des Jahres",
                            date(2117, 2, 1))
        self._extract_date("im zweiten Monat des Jahres 2023",
                            date(2023, 2, 1))
        self._extract_date("im nächsten Monat",
                            date(2117, 3, 1))
        self._extract_date("Mitte nächsten Monats",
                            date(2117, 3, 16))
        self._extract_date("Mitte des Monats",
                            date(2117, 2, 15))
        self._extract_date("Ende nächsten Monats",
                            date(2117, 3, 31))
        self._extract_date("im letzten Monat",
                            date(2117, 1, 1))
        self._extract_date("im nächsten Monat am 15.",
                            date(2117, 3, 15))
        self._extract_date("im letzten Monat am 15.",
                            date(2117, 1, 15))
        
    def test_extract_date_month_of(self):
        self._extract_date("am elften des monats",
                           date(2117, 2, 11))
        self._extract_date("am elften des monats Mai",
                           date(2117, 5, 11))
        self._extract_date("am elften des monats Mai 2023",
                           date(2023, 5, 11))
    
    def test_extract_date_month_relative(self):
        self._extract_date("in zwei Monaten",
                           date(2117, 4, 3))
        self._extract_date("vor zwei Monaten",
                           date(2116, 12, 3))
        self._extract_date("in zwei Monaten am 15.",
                           date(2117, 4, 15))
        self._extract_date("vor zwei Monaten am 15.",
                           date(2116, 12, 15))
        self._extract_date("zwei Monate nach dem 15. Mai",
                           date(2117, 7, 15))
        self._extract_date("zwei Monate vor dem 15. Mai",
                           date(2117, 3, 15))
    
    def test_extract_date_year(self):
        self._extract_date("im Jahr",
                           date(2117, 1, 1))
        self._extract_date("im Jahr 2023",
                           date(2023, 1, 1))
        self._extract_date("im nächsten Jahr",
                           date(2118, 1, 1))
        self._extract_date("im letzten Jahr",
                           date(2116, 1, 1))
        self._extract_date("letzten Jahres",
                           date(2116, 1, 1))
        self._extract_date("im Jahr 2023 am 15. Mai",
                           date(2023, 5, 15))
        
    def test_extract_date_year_of(self):
        pass

    def test_extract_date_year_relative(self):
        self._extract_date("in zwei Jahren",
                           date(2119, 2, 3))
        self._extract_date("vor zwei Jahren",
                           date(2115, 2, 3))
        self._extract_date("in 2 Jahren am 15. Mai",
                           date(2119, 5, 15))
        self._extract_date("am 15. Mai in 2 Jahren",
                           date(2119, 5, 15))
    
    def test_extract_date_season(self):
        # NOTE: astronomical date by default; utc to not have to deal with day shifts
        anchor = datetime(2022, 1, 1, 0, 0, tzinfo=timezone.utc)
        present_year = now_local().year
        self._extract_date("im Frühling",
                           date(2022, 3, 20),
                           anchor=anchor)
        self._extract_date("im Sommer",
                           date(2022, 6, 21),
                           anchor=anchor)
        self._extract_date("im Herbst",
                           date(2022, 9, 23),
                           anchor=anchor)
        self._extract_date("im Winter",
                           date(2022, 12, 21),
                           anchor=anchor)
        # note reference date is in that season -> diesen winter
        self._extract_date("im Winter",
                           date(present_year-1, 12, 21) if present_year != 2024 else
                           date(present_year-1, 12, 22),
                           anchor=datetime(present_year, 1, 1, 0, 0, tzinfo=timezone.utc))
        self._extract_date("im Frühling",
                           date(2022, 9, 23),
                           anchor=anchor,
                           hemi=Hemisphere.SOUTH)
        self._extract_date("im Sommer",
                           date(2022, 12, 21),
                           anchor=anchor,
                           hemi=Hemisphere.SOUTH)
        # note reference date is in that season -> diesen sommer
        self._extract_date("im Sommer",
                           date(present_year-1, 12, 21) if present_year != 2024 else
                           date(present_year-1, 12, 22),
                           anchor=datetime(present_year, 1, 1, 0, 0, tzinfo=timezone.utc),
                           hemi=Hemisphere.SOUTH)
        self._extract_date("im Winter",
                           date(2022, 6, 21),
                           anchor=anchor,
                           hemi=Hemisphere.SOUTH)
        self._extract_date("im Herbst",
                           date(2022, 3, 20),
                           anchor=anchor,
                           hemi=Hemisphere.SOUTH)
        self._extract_date("im Winter auf der südhalbkugel",
                           date(2022, 6, 21),
                           anchor=anchor,
                           hemi=None)
        self._extract_date("im Frühling auf der südhalbkugel",
                           date(2022, 9, 23),
                           anchor=anchor,
                           hemi=None)
        self._extract_date("im Sommer auf der südhalbkugel",
                           date(2022, 12, 21),
                           anchor=anchor,
                           hemi=None)
        self._extract_date("im Herbst auf der südhalbkugel",
                           date(2022, 3, 20),
                           anchor=anchor,
                           hemi=None)
        self._extract_date("kommenden Winter",
                           date(2022, 12, 21),
                           anchor=anchor)
        self._extract_date("im nächsten Frühling",
                           date(2022, 3, 20),
                           anchor=anchor)
        self._extract_date("im letzten Sommer",
                           date(2021, 6, 21),
                           anchor=anchor)
        self._extract_date("im Frühling 2023",
                           date(2023, 3, 20))
        self._extract_date("im nächsten Sommer",
                           date(2022, 6, 21),
                           anchor=anchor)
        self._extract_date("im Frühling nächsten Jahres",
                           date(2023, 3, 20),
                           anchor=anchor)
        self._extract_date("im Frühling letzten Jahres",
                           date(2021, 3, 20),
                           anchor=anchor)
        self._extract_date("Ende des Sommers",
                           date(2022, 9, 23),
                           anchor=anchor)
        self._extract_date("Mitte des Sommers",
                           date(2022, 8, 7),
                           anchor=anchor)
        self._extract_date("Anfang des Sommers",
                           date(2022, 6, 21),
                           anchor=anchor)
        # override 
        self._extract_date("im nächsten Sommer am 15. Mai",
                           date(2022, 5, 15),
                           anchor=anchor)
        self._extract_date("15. Mai im nächsten Sommer",
                           date(2022, 5, 15),
                           anchor=anchor)
        self._extract_date("im letzten Sommer am 15. Mai",
                           date(2021, 5, 15),
                           anchor=anchor)
        
        # metereological (as anchor is outside the defined astro range)
        self._extract_date("im Frühling",
                           date(2117, 3, 1))
        self._extract_date("im Sommer",
                           date(2117, 6, 1))
        self._extract_date("im Herbst",
                           date(2117, 9, 1))
        self._extract_date("im Winter",
                           date(2117, 12, 1))
    
    def test_extract_date_season_relative(self):
        anchor = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)
        self._extract_date("Frühling in einem Jahr",
                           date(2025, 3, 20),
                           anchor=anchor)
        self._extract_date("Frühling vor einem Jahr",
                           date(2023, 3, 20),
                           anchor=anchor)
        self._extract_date("im Winter vor einem Jahr",
                           date(2023, 12, 21),
                           anchor=anchor)
    
    def test_extract_date_season_of(self):
        anchor = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)
        self._extract_date("zehnter tag des Sommers",
                           date(2024, 6, 29),
                           anchor=anchor)
        self._extract_date("zweiten Monat im Sommer",
                           date(2024, 8, 1),
                           anchor=anchor)
        self._extract_date("zweiten woche im Sommer 2023",
                           date(2023, 7, 3),
                           anchor=anchor)
        self._extract_date("im Frühling des Jahres 2023",
                           date(2023, 3, 20),
                           anchor=anchor)
        
    def test_extract_date_named(self):
        self._extract_date("am Tag der Arbeit",
                           date(2117, 5, 1))
        self._extract_date("am Tag der Deutschen Einheit",
                           date(2117, 10, 3))
        self._extract_date("am Tag der Deutschen Einheit 2023",
                           date(2023, 10, 3))
        self._extract_date("Letzte Ostern",
                           date(2023, 4, 9),
                           anchor=datetime(2024, 1, 1, 0, 0))
        self._extract_date("Nächste Ostern",
                           date(2024, 3, 31),
                           anchor=datetime(2024, 1, 1, 0, 0))
        self._extract_date("Karfreitag",
                           date(2023, 4, 7),
                           anchor=datetime(2023, 1, 1, 0, 0))
        self._extract_date("Oktoberfest",
                           date(2023, 9, 16),
                           anchor=datetime(2023, 1, 1, 0, 0))
    
    def test_extract_date_named_relative(self):
        self._extract_date("Tag der Arbeit in einem Jahr",
                           date(2118, 5, 1))
        self._extract_date("Tag der Arbeit vor einem Jahr",
                           date(2116, 5, 1))
        self._extract_date("3 Tage vor dem ersten Advent",
                           date(2023, 11, 30),
                           anchor=datetime(2023, 1, 1, 0, 0))
        self._extract_date("3 Tage nach Weihnachten",
                           date(2023, 12, 27),
                           anchor=datetime(2023, 1, 1, 0, 0))
    
    def test_extract_date_named_of(self):
        # self._extract_date("Erste Woche im metereologischen Sommer",
        #                     date(2117, 6, 1))
        self._extract_date("Zweite Woche des Oktoberfests",
                           date(2117, 9, 25))
        self._extract_date("Zweite Woche des Oktoberfests 2024",
                           date(2024, 9, 21))
        self._extract_date("Dritter Tag im Advent",
                           date(2117, 11, 30))
        self._extract_date("Dritter Tag des letzten Advent",
                           date(2116, 12, 1))
    
    def test_extract_date_eras(self):
        self._extract_date("2460152.5 julianische tage",
                           date(2023, 7, 27))
        self._extract_date("2460152.5 JD",
                           date(2023, 7, 27))
        self._extract_date("2465 JDM",
                           None)      
        self._extract_date("160993 lilianische tage",
                           date(2023, 7, 27))
        self._extract_date("160993 LD",
                           date(2023, 7, 27))
        self._extract_date("1690464829 in unix zeit",
                           date(2023, 7, 27))
        self._extract_date("738730 ratadie",
                           date(2023, 7, 29))
        self._extract_date("738730 R.D.",
                           date(2023, 7, 29))
        self._extract_date("2023 nach Christus",
                           date(2023, 1, 1))
        self._extract_date("2023 anno domini",
                           date(2023, 1, 1))
        self._extract_date("2023 n. Chr.",
                           date(2023, 1, 1))
        self._extract_date("2. Jahrzehnt nach Christus",
                           date(10, 1, 1))
        self._extract_date("2. Jahrzehnt a.d.",
                           date(10, 1, 1))
        self._extract_date("2. Jahrzehnt der altarmenischen epoche",
                           date(562, 1, 1))
        self._extract_date("2. Jahrzehnt des persischen Kalenders",
                           date(642, 6, 16))
        self._extract_date("2. Jahrzehnt der badi ära",
                           date(1854, 3, 21))
        self._extract_date("2. Jahrzehnt der diokletianischen ära",
                           date(294, 8, 29))


if __name__ == '__main__':
    unittest.main() # pragma: no cover
