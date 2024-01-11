import unittest

from ovos_classifiers.heuristics.time import GermanTimeTagger, EnglishTimeTagger
from ovos_classifiers.heuristics.time_helpers import get_week_range, date_to_season, \
    get_weekend_range
from dateutil.relativedelta import relativedelta
from datetime import timedelta, datetime, date, time, timezone
from ovos_classifiers.heuristics.time_helpers import DurationResolution, \
    DateTimeResolution, Hemisphere, Season
from ovos_utils.time import DAYS_IN_1_MONTH, DAYS_IN_1_YEAR, now_local


class TestAEnglish(unittest.TestCase):
    def setUp(self):
        self.tagger = EnglishTimeTagger()
        self.ref_date = datetime(2117, 2, 3, 12, 0)
        self.now = now_local()
        self.default_time = self.now.time()

    def test_extract_durations_us(self):
        # defaulting to DurationResolution.TIMEDELTA
        def testExtract(text, expected_durations, expected_tokens,
                        resolution=DurationResolution.TIMEDELTA,
                        almostEqual=False):

            _durations = \
                self.tagger.extract_durations(text, resolution=resolution)
            
            durations = [dur.value for dur in _durations]
            
            self.assertEqual(len(durations), len(expected_durations))
            if almostEqual:
                for duration, expected_duration in zip(durations, expected_durations):
                    self.assertAlmostEqual(duration, expected_duration, places=2)
            else:
                for duration, expected_duration in zip(durations, expected_durations):
                    self.assertEqual(duration, expected_duration)

            for tokens, expected_length in zip(_durations, expected_tokens):
                self.assertEqual(len(tokens.word_list), expected_length)
    
        ## DurationResolution.TIMEDELTA
        testExtract("10 seconds", [timedelta(seconds=10.0)], [2])
        testExtract("5 minutes", [timedelta(minutes=5)], [2])
        testExtract("2 hours", [timedelta(hours=2)], [2])
        testExtract("3 days", [timedelta(days=3)], [2])
        testExtract("25 weeks", [timedelta(weeks=25)], [2])
        testExtract("seven hours", [timedelta(hours=7)], [2])
        testExtract("7.5 seconds", [timedelta(seconds=7.5)], [2])
        testExtract("eight and a half days thirty nine seconds",
                    [timedelta(days=8.5, seconds=39)], [4])
        testExtract("Set a timer for 30 minutes", [timedelta(minutes=30)], [2])
        testExtract("Four and a half minutes until sunset",
                    [timedelta(minutes=4.5)], [2])
        testExtract("Nineteen minutes past the hour",
                    [timedelta(minutes=19)], [2])
        testExtract("wake me up in three weeks, four hundred ninety seven days"
                    " and three hundred 91.6 seconds",
                    [timedelta(weeks=3, days=497, seconds=391.6)], [8])
        testExtract("The movie is one hour, fifty seven and a half minutes long",
                    [timedelta(hours=1, minutes=57.5)], [5])
        # TODO fix this
        # testExtract("10-seconds", [timedelta(seconds=10.0)], [2])
        # testExtract("5-minutes", [timedelta(minutes=5)], [2])
        testExtract("1 month", [timedelta(days=DAYS_IN_1_MONTH)], [2])
        testExtract("3 months", [timedelta(days=DAYS_IN_1_MONTH * 3)], [2])
        testExtract("a year", [timedelta(days=DAYS_IN_1_YEAR)], [2])
        testExtract("1 year", [timedelta(days=DAYS_IN_1_YEAR * 1)], [2])
        testExtract("5 years", [timedelta(days=DAYS_IN_1_YEAR * 5)], [2])
        testExtract("a decade", [timedelta(days=DAYS_IN_1_YEAR * 10)], [2])
        testExtract("1 decade", [timedelta(days=DAYS_IN_1_YEAR * 10)], [2])
        testExtract("5 decades", [timedelta(days=DAYS_IN_1_YEAR * 10 * 5)], [2])
        testExtract("1 century", [timedelta(days=DAYS_IN_1_YEAR * 100)], [2])
        testExtract("a century", [timedelta(days=DAYS_IN_1_YEAR * 100)], [2])
        testExtract("5 centuries", [timedelta(days=DAYS_IN_1_YEAR * 100 * 5)], [2])
        testExtract("1 millennium", [timedelta(days=DAYS_IN_1_YEAR * 1000)], [2])
        testExtract("5 millenniums", [timedelta(days=DAYS_IN_1_YEAR * 1000 * 5)], [2])
        
        ## DurationResolution.RELATIVEDELTA
        testExtract("10 seconds", [relativedelta(seconds=10.0)], [2],
                    resolution=DurationResolution.RELATIVEDELTA)
        testExtract("5 minutes", [relativedelta(minutes=5)], [2],
                    resolution=DurationResolution.RELATIVEDELTA)
        testExtract("2 hours", [relativedelta(hours=2)], [2],
                    resolution=DurationResolution.RELATIVEDELTA)
        testExtract("3 days", [relativedelta(days=3)], [2],
                    resolution=DurationResolution.RELATIVEDELTA)
        testExtract("25 weeks", [relativedelta(weeks=25)], [2],
                    resolution=DurationResolution.RELATIVEDELTA)
        testExtract("seven hours", [relativedelta(hours=7)], [2],
                    resolution=DurationResolution.RELATIVEDELTA)
        testExtract("7.5 seconds", [relativedelta(seconds=7.5)], [2],
                    resolution=DurationResolution.RELATIVEDELTA)
        testExtract("eight and a half days thirty nine seconds",
                    [relativedelta(days=8.5, seconds=39)], [4],
                    resolution=DurationResolution.RELATIVEDELTA)
        testExtract("Set a timer for 30 minutes",
                    [relativedelta(minutes=30)], [2],
                    resolution=DurationResolution.RELATIVEDELTA)
        testExtract("Four and a half minutes until sunset",
                    [relativedelta(minutes=4.5)], [2],
                    resolution=DurationResolution.RELATIVEDELTA),
        testExtract("Nineteen minutes past the hour",
                    [relativedelta(minutes=19)], [2],
                    resolution=DurationResolution.RELATIVEDELTA)
        testExtract("wake me up in three weeks, four hundred "
                    "ninety seven days and three hundred 91.6 seconds",
                    [relativedelta(weeks=3, days=497, seconds=391.6)], [8],
                    resolution=DurationResolution.RELATIVEDELTA)
        testExtract("The movie is one hour, fifty seven and a half minutes long",
                    [relativedelta(hours=1, minutes=57.5)], [5],
                    resolution=DurationResolution.RELATIVEDELTA)
        # testExtract("10-seconds", [relativedelta(seconds=10.0)], [1],
        #             resolution=DurationResolution.RELATIVEDELTA)
        # testExtract("5-minutes", [relativedelta(minutes=5)], [1],
        #             resolution=DurationResolution.RELATIVEDELTA)
        testExtract("1 month", [relativedelta(months=1)], [2],
                    resolution=DurationResolution.RELATIVEDELTA)
        testExtract("3 months", [relativedelta(months=3)], [2],
                    resolution=DurationResolution.RELATIVEDELTA)
        testExtract("a year", [relativedelta(years=1)], [2],
                    resolution=DurationResolution.RELATIVEDELTA)
        testExtract("1 year", [relativedelta(years=1)], [2],
                    resolution=DurationResolution.RELATIVEDELTA)
        testExtract("5 years", [relativedelta(years=5)], [2],
                    resolution=DurationResolution.RELATIVEDELTA)
        testExtract("a decade", [relativedelta(years=10)], [2],
                    resolution=DurationResolution.RELATIVEDELTA)
        testExtract("1 decade", [relativedelta(years=10)], [2],
                    resolution=DurationResolution.RELATIVEDELTA)
        testExtract("5 decades", [relativedelta(years=10 * 5)], [2],
                    resolution=DurationResolution.RELATIVEDELTA)
        testExtract("1 century", [relativedelta(years=100)], [2],
                    resolution=DurationResolution.RELATIVEDELTA)
        testExtract("a century", [relativedelta(years=100)], [2],
                    resolution=DurationResolution.RELATIVEDELTA)
        testExtract("5 centuries", [relativedelta(years=100 * 5)], [2],
                    resolution=DurationResolution.RELATIVEDELTA)
        testExtract("1 millennium", [relativedelta(years=1000)], [2],
                    resolution=DurationResolution.RELATIVEDELTA)
        testExtract("5 millennia", [relativedelta(years=1000 * 5)], [2],
                    resolution=DurationResolution.RELATIVEDELTA)
        
        def test_microseconds(duration_str, expected_durations,
                              expected_tokens):
            testExtract(duration_str, expected_durations, expected_tokens,
                        resolution=DurationResolution.TOTAL_MICROSECONDS,
                        almostEqual=True)

        test_microseconds("0.01 microseconds", [0.01], [2])
        test_microseconds("1 microsecond", [1], [2])
        test_microseconds("5 microseconds", [5], [2])
        test_microseconds("1 millisecond", [1 * 1000], [2])
        test_microseconds("5 milliseconds", [5 * 1000], [2])
        test_microseconds("100 milliseconds", [100 * 1000], [2])
        test_microseconds("1 second", [1000 * 1000], [2])
        test_microseconds("10 seconds", [10 * 1000 * 1000], [2])
        test_microseconds("5 minutes", [5 * 60 * 1000 * 1000], [2])
        test_microseconds("2 hours", [2 * 60 * 60 * 1000 * 1000], [2])
        test_microseconds("3 days", [3 * 24 * 60 * 60 * 1000 * 1000], [2])
        test_microseconds("25 weeks", [25 * 7 * 24 * 60 * 60 * 1000 * 1000], [2])
        test_microseconds("seven hours", [7 * 60 * 60 * 1000 * 1000], [2])
        test_microseconds("7.5 seconds", [7.5 * 1000 * 1000], [2])
        test_microseconds("eight and a half days thirty nine seconds",
                    [(8.5 * 24 * 60 * 60 + 39) * 1000 * 1000], [4])
        test_microseconds("Set a timer for 30 seconds",
                    [30 * 1000 * 1000], [2])
        test_microseconds("Four and a half minutes until sunset",
                    [4.5 * 60 * 1000 * 1000], [2])
        test_microseconds("Nineteen minutes past the hour",
                    [19 * 60 * 1000 * 1000], [2])
        # test_microseconds("10-seconds", [10 * 1000 * 1000], [1])
        # test_microseconds("5-minutes", [5 * 60 * 1000 * 1000], [1])
        test_microseconds("1 month", 
                    [DAYS_IN_1_MONTH * 24 * 60 * 60 * 1000 * 1000], [2])
        test_microseconds("3 months",
                    [3 * DAYS_IN_1_MONTH * 24 * 60 * 60 * 1000 * 1000], [2])
        test_microseconds("a year",
                    [DAYS_IN_1_YEAR * 24 * 60 * 60 * 1000 * 1000], [2])

        def test_milliseconds(duration_str, expected_durations,
                              expected_tokens):
            testExtract(duration_str, expected_durations, expected_tokens,
                        resolution=DurationResolution.TOTAL_MILLISECONDS,
                        almostEqual=True)

        test_milliseconds("1 microsecond", [0], [2])
        test_milliseconds("4.9 microseconds", [0], [2])
        test_milliseconds("5 microseconds", [0.005], [2])
        test_milliseconds("1 millisecond", [1], [2])
        test_milliseconds("5 milliseconds", [5], [2])
        test_milliseconds("100 milliseconds", [100], [2])
        test_milliseconds("1 second", [1000], [2])
        test_milliseconds("10 seconds", [10 * 1000], [2])
        test_milliseconds("5 minutes", [5 * 60 * 1000], [2])
        test_milliseconds("2 hours", [2 * 60 * 60 * 1000], [2])
        test_milliseconds("3 days", [3 * 24 * 60 * 60 * 1000], [2])
        test_milliseconds("25 weeks", [25 * 7 * 24 * 60 * 60 * 1000], [2])
        test_milliseconds("seven hours", [7 * 60 * 60 * 1000], [2])
        test_milliseconds("7.5 seconds", [7.5 * 1000], [2])
        test_milliseconds("eight and a half days thirty nine seconds",
                          [(8.5 * 24 * 60 * 60 + 39) * 1000], [4])
        test_milliseconds("Set a timer for 30 minutes", [30 * 60 * 1000],
                          [2])
        test_milliseconds("Four and a half minutes until sunset",
                          [4.5 * 60 * 1000], [2])
        test_milliseconds("Nineteen minutes past the hour", [19 * 60 * 1000],
                          [2])
        test_milliseconds(
            "wake me up in three weeks, four hundred ninety seven "
            "days and three hundred 91.6 seconds",
            [(3 * 7 * 24 * 60 * 60 + 497 * 24 * 60 * 60 + 391.6) * 1000],
            [8])
        test_milliseconds("The movie is one hour, fifty seven and a half "
                          "minutes long", [(60 * 60 + 57.5 * 60) * 1000], [5])
        # test_milliseconds("10-seconds", [10 * 1000], [2])
        # test_milliseconds("5-minutes", [5 * 60 * 1000], [2])
        test_milliseconds("1 month", [DAYS_IN_1_MONTH * 24 * 60 * 60 * 1000], [2])
        test_milliseconds("3 months",
                          [3 * DAYS_IN_1_MONTH * 24 * 60 * 60 * 1000], [2])
        test_milliseconds("a year", [DAYS_IN_1_YEAR * 24 * 60 * 60 * 1000], [2])
        test_milliseconds("1 year", [DAYS_IN_1_YEAR * 24 * 60 * 60 * 1000], [2])
        test_milliseconds("5 years", [5 * DAYS_IN_1_YEAR * 24 * 60 * 60 * 1000], [2])
        test_milliseconds("a decade",
                          [10 * DAYS_IN_1_YEAR * 24 * 60 * 60 * 1000], [2])
        test_milliseconds("1 decade",
                          [10 * DAYS_IN_1_YEAR * 24 * 60 * 60 * 1000], [2])
        test_milliseconds("5 decades",
                          [5 * 10 * DAYS_IN_1_YEAR * 24 * 60 * 60 * 1000], [2])
        test_milliseconds("1 century",
                          [100 * DAYS_IN_1_YEAR * 24 * 60 * 60 * 1000], [2])
        test_milliseconds("a century",
                          [100 * DAYS_IN_1_YEAR * 24 * 60 * 60 * 1000], [2])
        test_milliseconds("5 centuries",
                          [500 * DAYS_IN_1_YEAR * 24 * 60 * 60 * 1000], [2])
        test_milliseconds("1 millennium",
                          [1000 * DAYS_IN_1_YEAR * 24 * 60 * 60 * 1000], [2])
        test_milliseconds("5 millenniums",
                          [5000 * DAYS_IN_1_YEAR * 24 * 60 * 60 * 1000], [2])

        def test_seconds(duration_str, expected_durations,
                              expected_tokens):
            testExtract(duration_str, expected_durations, expected_tokens,
                        resolution=DurationResolution.TOTAL_SECONDS,
                        almostEqual=True)

        test_seconds("1 millisecond", [0], [2])
        test_seconds("4 milliseconds", [0], [2])
        test_seconds("5 milliseconds", [0.005], [2])
        test_seconds("100 milliseconds", [0.1], [2])
        test_seconds("10 seconds", [10], [2])
        test_seconds("5 minutes", [5 * 60], [2])
        test_seconds("2 hours", [2 * 60 * 60], [2])
        test_seconds("3 days", [3 * 24 * 60 * 60], [2])
        test_seconds("25 weeks", [25 * 7 * 24 * 60 * 60], [2])
        test_seconds("seven hours", [7 * 60 * 60], [2])
        test_seconds("7.5 seconds", [7.5], [2])
        test_seconds("eight and a half days thirty nine seconds",
                     [8.5 * 24 * 60 * 60 + 39], [4])
        test_seconds("Set a timer for 30 minutes", [30 * 60], [2])
        test_seconds("Four and a half minutes until sunset", [4.5 * 60], [2])
        test_seconds("Nineteen minutes past the hour", [19 * 60], [2])
        test_seconds("wake me up in three weeks, four hundred ninety seven days"
                     " and three hundred 91.6 seconds",
                    [3 * 7 * 24 * 60 * 60 + 497 * 24 * 60 * 60 + 391.6], [8])
        test_seconds("The movie is one hour, fifty seven and a half minutes long",
                     [60 * 60 + 57.5 * 60], [5])
        # test_seconds("10-seconds", [10], [2])
        # test_seconds("5-minutes", [5 * 60], [2])
        test_seconds("1 month", [DAYS_IN_1_MONTH * 24 * 60 * 60], [2])
        test_seconds("3 months", [3 * DAYS_IN_1_MONTH * 24 * 60 * 60], [2])
        test_seconds("a year", [DAYS_IN_1_YEAR * 24 * 60 * 60], [2])
        test_seconds("1 year", [DAYS_IN_1_YEAR * 24 * 60 * 60], [2])
        test_seconds("5 years", [5 * DAYS_IN_1_YEAR * 24 * 60 * 60], [2])
        test_seconds("a decade", [10 * DAYS_IN_1_YEAR * 24 * 60 * 60], [2])
        test_seconds("1 decade", [10 * DAYS_IN_1_YEAR * 24 * 60 * 60], [2])
        test_seconds("5 decades", [5 * 10 * DAYS_IN_1_YEAR * 24 * 60 * 60], [2])
        test_seconds("1 century", [100 * DAYS_IN_1_YEAR * 24 * 60 * 60], [2])
        test_seconds("a century", [100 * DAYS_IN_1_YEAR * 24 * 60 * 60], [2])
        test_seconds("5 centuries", [500 * DAYS_IN_1_YEAR * 24 * 60 * 60], [2])
        test_seconds("1 millennium", [1000 * DAYS_IN_1_YEAR * 24 * 60 * 60], [2])
        test_seconds("5 millenniums", [5000 * DAYS_IN_1_YEAR * 24 * 60 * 60], [2])

        def test_minutes(duration_str, expected_durations,
                              expected_tokens):
            testExtract(duration_str, expected_durations, expected_tokens,
                        resolution=DurationResolution.TOTAL_MINUTES,
                        almostEqual=True)

        test_minutes("10 seconds", [10 / 60], [2])
        test_minutes("5 minutes", [5], [2])
        test_minutes("2 hours", [2 * 60], [2])
        test_minutes("3 days", [3 * 24 * 60], [2])
        test_minutes("25 weeks", [25 * 7 * 24 * 60], [2])
        test_minutes("seven hours", [7 * 60], [2])
        test_minutes("7.5 seconds", [7.5 / 60], [2])
        test_minutes("eight and a half days thirty nine seconds",
                    [8.5 * 24 * 60 + 39 / 60], [4])
        test_minutes("Set a timer for 30 minutes", [30], [2])
        test_minutes("Four and a half minutes until sunset", [4.5], [2])
        test_minutes("Nineteen minutes past the hour", [19], [2])
        test_minutes("wake me up in three weeks, four hundred ninety seven "
                    "days and three hundred 91.6 seconds",
                    [3 * 7 * 24 * 60 + 497 * 24 * 60 + 391.6 / 60], [8])
        test_minutes("The movie is one hour, fifty seven and a half "
                     "minutes long", [60 + 57.5], [5])
        # test_minutes("10-seconds", [10 / 60], [2])
        # test_minutes("5-minutes", [5], [2])
        test_minutes("1 month", [DAYS_IN_1_MONTH * 24 * 60], [2])
        test_minutes("3 months", [3 * DAYS_IN_1_MONTH * 24 * 60], [2])
        test_minutes("a year", [DAYS_IN_1_YEAR * 24 * 60], [2])
        test_minutes("1 year", [DAYS_IN_1_YEAR * 24 * 60], [2])
        test_minutes("5 years", [5 * DAYS_IN_1_YEAR * 24 * 60], [2])
        test_minutes("a decade", [10 * DAYS_IN_1_YEAR * 24 * 60], [2])
        test_minutes("1 decade", [10 * DAYS_IN_1_YEAR * 24 * 60], [2])
        test_minutes("5 decades", [5 * 10 * DAYS_IN_1_YEAR * 24 * 60], [2])
        test_minutes("1 century", [100 * DAYS_IN_1_YEAR * 24 * 60], [2])
        test_minutes("a century", [100 * DAYS_IN_1_YEAR * 24 * 60], [2])
        test_minutes("5 centuries", [500 * DAYS_IN_1_YEAR * 24 * 60], [2])
        test_minutes("1 millennium", [1000 * DAYS_IN_1_YEAR * 24 * 60], [2])
        test_minutes("5 millenniums", [5000 * DAYS_IN_1_YEAR * 24 * 60], [2])

        def test_hours(duration_str, expected_durations,
                              expected_tokens):
            testExtract(duration_str, expected_durations, expected_tokens,
                        resolution=DurationResolution.TOTAL_HOURS,
                        almostEqual=True)

        test_hours("10 seconds", [0], [2])
        test_hours("17.9 seconds", [0], [2])
        test_hours("5 minutes", [5 / 60], [2])
        test_hours("2 hours", [2], [2])
        test_hours("3 days", [3 * 24], [2])
        test_hours("25 weeks", [25 * 7 * 24], [2])
        test_hours("seven hours", [7], [2])
        test_hours("7.5 seconds", [0], [2])
        test_hours("eight and a half days thirty nine seconds",
                [8.5 * 24 + 39 / 60 / 60], [4])
        test_hours("Set a timer for 30 minutes", [30 / 60], [2])
        test_hours("Four and a half minutes until sunset", [4.5 / 60], [2])
        test_hours("Nineteen minutes past the hour", [19 / 60], [2])
        test_hours("wake me up in three weeks, four hundred ninety seven "
                   "days and three hundred 91.6 seconds",
                   [3 * 7 * 24 + 497 * 24 + 391.6 / 60 / 60], [8])
        test_hours("The movie is one hour, fifty seven and a half "
                   "minutes long", [1 + 57.5 / 60], [5])
        # test_hours("10-seconds", [0], [2])
        # test_hours("5-minutes", [5 / 60], [2])
        test_hours("1 month", [DAYS_IN_1_MONTH * 24], [2])
        test_hours("3 months", [3 * DAYS_IN_1_MONTH * 24], [2])
        test_hours("a year", [DAYS_IN_1_YEAR * 24], [2])
        test_hours("1 year", [DAYS_IN_1_YEAR * 24], [2])
        test_hours("5 years", [5 * DAYS_IN_1_YEAR * 24], [2])
        test_hours("a decade", [10 * DAYS_IN_1_YEAR * 24], [2])
        test_hours("1 decade", [10 * DAYS_IN_1_YEAR * 24], [2])
        test_hours("5 decades", [5 * 10 * DAYS_IN_1_YEAR * 24], [2])
        test_hours("1 century", [100 * DAYS_IN_1_YEAR * 24], [2])
        test_hours("a century", [100 * DAYS_IN_1_YEAR * 24], [2])
        test_hours("5 centuries", [500 * DAYS_IN_1_YEAR * 24], [2])
        test_hours("1 millennium", [1000 * DAYS_IN_1_YEAR * 24], [2])
        test_hours("5 millenniums", [5000 * DAYS_IN_1_YEAR * 24], [2])

        def test_days(duration_str, expected_durations,
                              expected_tokens):
            testExtract(duration_str, expected_durations, expected_tokens,
                        resolution=DurationResolution.TOTAL_DAYS,
                        almostEqual=True)

        test_days("10 seconds", [0], [2])
        test_days("5 minutes", [0], [2])
        test_days("7.1 minutes", [0], [2])
        test_days("2 hours", [2 / 24], [2])
        test_days("3 days", [3], [2])
        test_days("25 weeks", [25 * 7], [2])
        test_days("seven hours", [7 / 24], [2])
        test_days("7.5 seconds", [0], [2])
        test_days("eight and a half days thirty nine seconds", [8.5], [4])
        test_days("Set a timer for 30 minutes", [30 / 60 / 24], [2])
        test_days("Four and a half minutes until sunset", [0], [2])
        test_days("Nineteen minutes past the hour", [19 / 60 / 24], [2])
        test_days("wake me up in three weeks, four hundred ninety seven "
                "days and three hundred 91.6 seconds",
                [3 * 7 + 497 + 391.6 / 60 / 60 / 24], [8])
        test_days("The movie is one hour, fifty seven and a half "
                  "minutes long", [1 / 24 + 57.5 / 60 / 24], [5])
        # test_days("10-seconds", [0], [2])
        # test_days("5-minutes", [0], [2])
        test_days("1 month", [DAYS_IN_1_MONTH], [2])
        test_days("3 months", [3 * DAYS_IN_1_MONTH], [2])
        test_days("a year", [DAYS_IN_1_YEAR], [2])
        test_days("1 year", [DAYS_IN_1_YEAR], [2])
        test_days("5 years", [5 * DAYS_IN_1_YEAR], [2])
        test_days("a decade", [10 * DAYS_IN_1_YEAR], [2])
        test_days("1 decade", [10 * DAYS_IN_1_YEAR], [2])
        test_days("5 decades", [5 * 10 * DAYS_IN_1_YEAR], [2])
        test_days("1 century", [100 * DAYS_IN_1_YEAR], [2])
        test_days("a century", [100 * DAYS_IN_1_YEAR], [2])
        test_days("5 centuries", [500 * DAYS_IN_1_YEAR], [2])
        test_days("1 millennium", [1000 * DAYS_IN_1_YEAR], [2])
        test_days("5 millenniums", [5000 * DAYS_IN_1_YEAR], [2])

        def test_weeks(duration_str, expected_durations,
                              expected_tokens):
            testExtract(duration_str, expected_durations, expected_tokens,
                        resolution=DurationResolution.TOTAL_WEEKS,
                        almostEqual=True)

        test_weeks("10 seconds", [0], [2])
        test_weeks("5 minutes", [0], [2])
        test_weeks("50 minutes", [0], [2])
        test_weeks("2 hours", [2 / 24 / 7], [2])
        test_weeks("3 days", [3 / 7], [2])
        test_weeks("25 weeks", [25], [2])
        test_weeks("seven hours", [7 / 24 / 7], [2])
        test_weeks("7.5 seconds", [7.5 / 60 / 60 / 24 / 7], [2])
        test_weeks("eight and a half days thirty nine seconds", [8.5 / 7], [4])
        test_weeks("Set a timer for 30 minutes", [0], [2])
        test_weeks("Four and a half minutes until sunset", [0], [2])
        test_weeks("Nineteen minutes past the hour", [0], [2])
        test_weeks("wake me up in three weeks, four hundred ninety seven "
                   "days and three hundred 91.6 seconds", [3 + 497 / 7], [8])
        test_weeks("The movie is one hour, fifty seven and a half "
                   "minutes long", [1 / 24 / 7 + 57.5 / 60 / 24 / 7], [5])
        # test_weeks("10-seconds", [0], [2])
        # test_weeks("5-minutes", [0], [2])
        test_weeks("1 month", [DAYS_IN_1_MONTH / 7], [2])
        test_weeks("3 months", [3 * DAYS_IN_1_MONTH / 7], [2])
        test_weeks("a year", [DAYS_IN_1_YEAR / 7], [2])
        test_weeks("1 year", [DAYS_IN_1_YEAR / 7], [2])
        test_weeks("5 years", [5 * DAYS_IN_1_YEAR / 7], [2])
        test_weeks("a decade", [10 * DAYS_IN_1_YEAR / 7], [2])
        test_weeks("1 decade", [10 * DAYS_IN_1_YEAR / 7], [2])
        test_weeks("5 decades", [5 * 10 * DAYS_IN_1_YEAR / 7], [2])
        test_weeks("1 century", [100 * DAYS_IN_1_YEAR / 7], [2])
        test_weeks("a century", [100 * DAYS_IN_1_YEAR / 7], [2])
        test_weeks("5 centuries", [500 * DAYS_IN_1_YEAR / 7], [2])
        test_weeks("1 millennium", [1000 * DAYS_IN_1_YEAR / 7], [2])
        test_weeks("5 millenniums", [5000 * DAYS_IN_1_YEAR / 7], [2])

        def test_months(duration_str, expected_durations,
                              expected_tokens):
            testExtract(duration_str, expected_durations, expected_tokens,
                        resolution=DurationResolution.TOTAL_MONTHS,
                        almostEqual=True)

        test_months("10 seconds", [0], [2])
        test_months("5 minutes", [0], [2])
        test_months("2 hours", [0], [2])
        test_months("3 days", [3/DAYS_IN_1_MONTH], [2])
        test_months("25 weeks", [25*7/DAYS_IN_1_MONTH], [2])
        test_months("seven hours", [7/24/DAYS_IN_1_MONTH], [2])
        test_months("7.5 seconds", [0], [2])
        test_months("eight and a half days thirty nine seconds", 
                    [8.5/DAYS_IN_1_MONTH], [4])
        test_months("Set a timer for 30 minutes", [0], [2])
        test_months("Four and a half minutes until sunset", [0], [2])
        test_months("Nineteen minutes past the hour", [0], [2])
        test_months("wake me up in three weeks, four hundred ninety seven days "
                    "and three hundred 91.6 seconds",
                    [3*7/DAYS_IN_1_MONTH + 497/DAYS_IN_1_MONTH], [8])
        test_months("The movie is one hour, fifty seven and a half minutes long",
                    [0], [5])
        # test_months("10-seconds", [0], [2])
        # test_months("5-minutes", [0], [2])
        test_months("1 month", [1], [2])
        test_months("3 months", [3], [2])
        test_months("a year", [DAYS_IN_1_YEAR/DAYS_IN_1_MONTH], [2])
        test_months("1 year", [DAYS_IN_1_YEAR/DAYS_IN_1_MONTH], [2])
        test_months("5 years", [5*DAYS_IN_1_YEAR/DAYS_IN_1_MONTH], [2])
        test_months("a decade", [10*DAYS_IN_1_YEAR/DAYS_IN_1_MONTH], [2])
        test_months("1 decade", [10*DAYS_IN_1_YEAR/DAYS_IN_1_MONTH], [2])
        test_months("5 decades", [5*10*DAYS_IN_1_YEAR/DAYS_IN_1_MONTH], [2])
        test_months("1 century", [100*DAYS_IN_1_YEAR/DAYS_IN_1_MONTH], [2])
        test_months("a century", [100*DAYS_IN_1_YEAR/DAYS_IN_1_MONTH], [2])
        test_months("5 centuries", [500*DAYS_IN_1_YEAR/DAYS_IN_1_MONTH], [2])
        test_months("1 millennium", [1000*DAYS_IN_1_YEAR/DAYS_IN_1_MONTH], [2])
        test_months("5 millenniums", [5000*DAYS_IN_1_YEAR/DAYS_IN_1_MONTH], [2])

        def test_years(duration_str, expected_durations,
                              expected_tokens):
            testExtract(duration_str, expected_durations, expected_tokens,
                        resolution=DurationResolution.TOTAL_YEARS,
                        almostEqual=True)

        test_years("10 seconds", [0], [2])
        test_years("5 minutes", [0], [2])
        test_years("2 hours", [0], [2])
        test_years("1.5 days", [0], [2])
        test_years("3 days", [3/DAYS_IN_1_YEAR], [2])
        test_years("25 weeks", [25*7/DAYS_IN_1_YEAR], [2])
        test_years("seven hours", [0], [2])
        test_years("7.5 seconds", [0], [2])
        test_years("eight and a half days thirty nine seconds",
                   [8.5/DAYS_IN_1_YEAR], [4])
        test_years("Set a timer for 30 minutes", [0], [2])
        test_years("Four and a half minutes until sunset", [0], [2])
        test_years("Nineteen minutes past the hour", [0], [2])
        test_years("wake me up in three weeks, four hundred ninety seven days"
                   " and three hundred 91.6 seconds",
                   [3*7/DAYS_IN_1_YEAR + 497/DAYS_IN_1_YEAR], [8])
        test_years("The movie is one hour, fifty seven and a half minutes long",
                   [0], [5])
        # test_years("10-seconds", [0], [2])
        # test_years("5-minutes", [0], [2])
        test_years("1 month", [1/12], [2])
        test_years("3 months", [3/12], [2])
        test_years("a year", [1], [2])
        test_years("1 year", [1], [2])
        test_years("5 years", [5], [2])
        test_years("a decade", [10], [2])
        test_years("1 decade", [10], [2])
        test_years("5 decades", [50], [2])
        test_years("1 century", [100], [2])
        test_years("a century", [100], [2])
        test_years("5 centuries", [500], [2])
        test_years("1 millennium", [1000], [2])
        test_years("5 millenniums", [5000], [2])

        def test_decades(duration_str, expected_durations,
                              expected_tokens):
            testExtract(duration_str, expected_durations, expected_tokens,
                        resolution=DurationResolution.TOTAL_DECADES,
                        almostEqual=True)

        test_decades("10 seconds", [0], [2])
        test_decades("5 minutes", [0], [2])
        test_decades("2 hours", [0], [2])
        test_decades("3 days", [0], [2])
        test_decades("25 weeks", [25*7/DAYS_IN_1_YEAR/10], [2])
        test_decades("seven hours", [0], [2])
        test_decades("7.5 seconds", [0], [2])
        test_decades("eight and a half days thirty nine seconds", [0], [4])
        test_decades("Set a timer for 30 minutes", [0], [2])
        test_decades("Four and a half minutes until sunset", [0], [2])
        test_decades("Nineteen minutes past the hour", [0], [2])
        test_decades("The movie is one hour, fifty seven and a half minutes long",
                     [0], [5])
        # test_decades("10-seconds", 0, [2])
        # test_decades("5-minutes", 0, [2])
        test_decades("1 month", [1/12/10], [2])
        test_decades("3 months", [3/12/10], [2])
        test_decades("a year", [1/10], [2])
        test_decades("1 year", [1/10], [2])
        test_decades("5 years", [5/10], [2])
        test_decades("a decade", [1], [2])
        test_decades("1 decade", [1], [2])
        test_decades("5 decades", [5], [2])
        test_decades("1 century", [10], [2])
        test_decades("a century", [10], [2])
        test_decades("5 centuries", [50], [2])
        test_decades("1 millennium", [100], [2])
        test_decades("5 millenniums", [500], [2])

        def test_centuries(duration_str, expected_durations,
                              expected_tokens):
            testExtract(duration_str, expected_durations, expected_tokens,
                        resolution=DurationResolution.TOTAL_CENTURIES,
                        almostEqual=True)

        test_centuries("10 seconds", [0], [2])
        test_centuries("5 minutes", [0], [2])
        test_centuries("2 hours", [0], [2])
        test_centuries("3 days", [0], [2])
        test_centuries("25 weeks", [0], [2])
        test_centuries("seven hours", [0], [2])
        test_centuries("7.5 seconds", [0], [2])
        test_centuries("eight and a half days thirty nine seconds", [0], [4])
        test_centuries("Set a timer for 30 minutes", [0], [2])
        test_centuries("Four and a half minutes until sunset", [0], [2])
        test_centuries("Nineteen minutes past the hour", [0], [2])
        test_centuries("The movie is one hour, fifty seven and a half minutes long",
                       [0], [5])
        test_centuries("1 month", [1/12/100], [2])
        test_centuries("3 months", [3/12/100], [2])
        test_centuries("a year", [1/100], [2])
        test_centuries("1 year", [1/100], [2])
        test_centuries("5 years", [5/100], [2])
        test_centuries("a decade", [1/10], [2])
        test_centuries("1 decade", [1/10], [2])
        test_centuries("5 decades", [5/10], [2])
        test_centuries("1 century", [1], [2])
        test_centuries("a century", [1], [2])
        test_centuries("5 centuries", [5], [2])
        test_centuries("1 millennium", [10], [2])
        test_centuries("5 millenniums", [50], [2])

        def test_millennium(duration_str, expected_durations,
                              expected_tokens):
            testExtract(duration_str, expected_durations, expected_tokens,
                        resolution=DurationResolution.TOTAL_MILLENNIUMS,
                        almostEqual=True)

        test_millennium("10 seconds", [0], [2])
        test_millennium("5 minutes", [0], [2])
        test_millennium("2 hours", [0], [2])
        test_millennium("3 days", [0], [2])
        test_millennium("25 weeks", [0], [2])
        test_millennium("seven hours", [0], [2])
        test_millennium("7.5 seconds", [0], [2])
        test_millennium("eight and a half days thirty nine seconds", [0], [4])
        test_millennium("Set a timer for 30 minutes", [0], [2])
        test_millennium("Four and a half minutes until sunset", [0], [2])
        test_millennium("Nineteen minutes past the hour", [0], [2])
        test_millennium("wake me up in three weeks, four hundred ninety seven days"
                        " and three hundred 91.6 seconds", [0], [8])
        test_millennium("The movie is one hour, fifty seven and a half minutes long",
                        [0], [5])
        # test_millennium("10-seconds", [0], [2])
        # test_millennium("5-minutes", [0], [2])
        test_millennium("1 month", [0], [2])
        test_millennium("3 months", [0], [2])
        test_millennium("6 months", [0], [2])
        test_millennium("a year", [0], [2])
        test_millennium("1 year", [0], [2])
        test_millennium("4.99 years", [0], [2])
        test_millennium("5 years", [5/1000], [2])
        test_millennium("a decade", [1/100], [2])
        test_millennium("1 decade", [1/100], [2])
        test_millennium("5 decades", [5/100], [2])
        test_millennium("1 century", [1/10], [2])
        test_millennium("a century", [1/10], [2])
        test_millennium("5 centuries", [5/10], [2])
        test_millennium("1 millennium", [1], [2])
        test_millennium("5 millenniums", [5], [2])
    
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
    
    def _extract_time(self,
                      time_str,
                      expected_time,
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

    def test_extract_time(self):
        self._extract_time("set alarm at 9:00 PM",
                           time(21, 0, 0))
        self._extract_time("set alarm at 9:00 AM",
                           time(9, 0, 0))
        self._extract_time("set alarm at 9:00 am",
                           time(9, 0, 0))
        self._extract_time("set alarm at 9:00 pm",
                           time(21, 0, 0))
        self._extract_time("set alarm at 9:00 p.m.",
                           time(21, 0, 0))
        self._extract_time("set alarm at 9:00 a.m.",
                           time(9, 0, 0))
        self._extract_time("set alarm at 9.00 PM",
                           time(21, 0, 0))
        self._extract_time("set alarm at 9 AM",
                           time(9, 0, 0))
        self._extract_time("set alarm at 9 30 am",
                           time(9, 30, 0))                               

    def test_extract_time_ambigiguous(self):
        self._extract_time("set alarm at 9 on weekdays",
                           time(9, 0, 0))
        self._extract_time("at 8 tonight",
                           time(20, 0, 0))
        # pm is split from the time during tokenization
        # ie not really a test for missing am/pm
        self._extract_time("for 8:30pm tonight",
                           time(20, 30, 0))
        # Tests a time with ':' & without am/pm
        self._extract_time("set an alarm for tonight 9:30",
                           time(21, 30, 0))
        self._extract_time("set an alarm at 9:00 for tonight",
                           time(21, 0, 0))
        # Check if it picks the intent irrespective of correctness
        self._extract_time("set an alarm at 9 o'clock for tonight",
                           time(21, 0, 0))
        self._extract_time("set an alarm at 9 30 o'clock tonight",
                           time(21, 30, 0))
        self._extract_time("remind me about the game tonight at 11:30",
                           time(23, 30, 0))
        self._extract_time("set alarm at 7:30 on weekdays",
                           time(7, 30, 0))
        self._extract_time("set alarm 9 30",
                           None)
    
    def test_extract_time_daytimes(self):
        self._extract_time("set alarm in the morning",
                           time(8, 0, 0))
        # day shift if the `time` is in the past and not specifically mentioned
        # TODO: -> extract_datetime test
        # _dt = self.tagger.extract_date("set alarm in the morning").value
        # self.assertEqual(_dt.weekday(), self.now.weekday() + 1)
        self._extract_time("set alarm in the afternoon",
                           time(15, 0, 0))
        self._extract_time("set alarm in the afternoon at 5",
                           time(17, 0, 0))
        self._extract_time("set alarm at 15:30 in the afternoon",
                           time(15, 30, 0))
        self._extract_time("set alarm in the evening",
                           time(19, 0, 0))
        self._extract_time("set alarm at night",
                           time(22, 0, 0))
        self._extract_time("set alarm at noon",
                           time(12, 0, 0))
        self._extract_time("set alarm at midnight",
                           time(0, 0, 0))

    def _extract_date(self,
                      date_str,
                      expected_date,
                      resolution=DateTimeResolution.DAY,
                      anchor=None,
                      hemi=Hemisphere.NORTH,
                      greedy=False):    
            anchor = anchor or self.ref_date
            if isinstance(expected_date, datetime):
                expected_date = expected_date.date()
            extracted_date = self.tagger.extract_date(date_str,
                                                      anchor,
                                                      resolution,
                                                      hemisphere=hemi,
                                                      greedy=greedy)
            if extracted_date is None:
                self.assertEqual(extracted_date, expected_date)
            else:
                self.assertEqual(extracted_date.value, expected_date)
    
    def test_extract_date_preformatted(self):

        # ISO 8601
        self._extract_date("It is 2001-2-12", date(2001, 2, 12))
        # american format
        self._extract_date("It is 02/12/2001", date(2001, 2, 12))
        self._extract_date("It is 2/12/2001", date(2001, 2, 12))
        self._extract_date("It is 2001/12/2", date(2001, 2, 12))
        # european format
        self._extract_date("It is 12.2.2001", date(2001, 2, 12))
        # non standard format, no disambiguation between day and month
        self._extract_date("It is 2-12-2001", date(2001, 12, 2))
        self._extract_date("It is 12-2-2001", date(2001, 2, 12))
        # .. until "month" is greater than 12
        self._extract_date("It is 2-13-2001", date(2001, 2, 13))

        self._extract_date("It is 99-99-2001", None)

    def test_extract_date_now(self):

        self._extract_date("now", self.now.date())
        self._extract_date("today", self.ref_date)
        self._extract_date("tomorrow", self.ref_date + relativedelta(days=1))
        self._extract_date("yesterday", self.ref_date - relativedelta(days=1))
        self._extract_date("twenty two thousand days before now",
                      self.now - relativedelta(days=22000))
        self._extract_date("10 days from now",
                      self.now + relativedelta(days=10))
        
    def test_extract_date_ago(self):

        self._extract_date("twenty two weeks ago",
                      self.ref_date - relativedelta(weeks=22))
        self._extract_date("twenty two months ago",
                      self.ref_date - relativedelta(months=22))
        self._extract_date("twenty two decades ago",
                      self.ref_date - relativedelta(years=10 * 22))
        self._extract_date("1 century ago",
                      self.ref_date - relativedelta(years=100))
        self._extract_date("ten centuries ago",
                      self.ref_date - relativedelta(years=1000))
        self._extract_date("two millenniums ago",
                      self.ref_date - relativedelta(years=2000))
        self._extract_date("twenty two thousand days ago",
                      self.ref_date - relativedelta(days=22000))
        # years BC not supported
        self.assertRaises(ValueError, self.tagger.extract_date,
                          "twenty two thousand years ago", self.ref_date)
        
    def test_extract_date_spoken_date(self):

        self._extract_date("13 may 1992", date(month=5, year=1992, day=13))
        self._extract_date("march 1st 2020", date(month=3, year=2020, day=1))
        self._extract_date("29 november", date(month=11,
                                          year=self.ref_date.year,
                                          day=29))
        self._extract_date("january 2020", date(month=1,
                                           year=2020,
                                           day=1))
        self._extract_date("day 1", date(month=self.ref_date.month,
                                    year=self.ref_date.year,
                                    day=1))
        self._extract_date("1st of september",
                      self.ref_date.replace(day=1, month=9,
                                            year=self.ref_date.year))
        self._extract_date("march 13th",
                      self.ref_date.replace(day=13, month=3,
                                            year=self.ref_date.year))
        self._extract_date("12 may",
                      self.ref_date.replace(day=12, month=5,
                                            year=self.ref_date.year))
        
    def test_extract_date_from(self):

        self._extract_date("10 days from today",
                      self.ref_date + relativedelta(days=10))
        self._extract_date("10 days from tomorrow",
                      self.ref_date + relativedelta(days=11))
        self._extract_date("10 days from yesterday",
                      self.ref_date + relativedelta(days=9))
        # self._test_date("10 days from after tomorrow",  # TODO fix me
        #          self.ref_date + relativedelta(days=12))

        # years > 9999 not supported
        self.assertRaises(ValueError, self.tagger.extract_date,
                          "twenty two thousand years from now", self.ref_date)
        
    def test_extract_date_ordinals(self):

        self._extract_date("the 5th day", self.ref_date.replace(day=5))
        self._extract_date("the fifth day",
                      date(month=self.ref_date.month,
                           year=self.ref_date.year, day=5))
        self._extract_date("the 20th day of 4th month",
                      self.ref_date.replace(month=4, day=20))
        self._extract_date("the 20th day of month 4",
                      self.ref_date.replace(month=4, day=20))
        self._extract_date("6th month of 1992", date(month=6, year=1992, day=1))
        self._extract_date("first day of the 10th month of 1969",
                      self.ref_date.replace(day=1, month=10, year=1969))
        self._extract_date("2nd day of 2020",
                      self.ref_date.replace(day=2, month=1, year=2020))
        self._extract_date("three hundredth day of 2020",
                      self.ref_date.replace(day=1, month=1, year=2020) +
                      relativedelta(days=299))
        
    def test_extract_date_plus(self):

        self._extract_date("now plus 10 days",
                      self.now + relativedelta(days=10))
        self._extract_date("today plus 10 days",
                      self.ref_date + relativedelta(days=10))
        self._extract_date("yesterday plus 10 days",
                      self.ref_date + relativedelta(days=9))
        self._extract_date("tomorrow plus 10 days",
                      self.ref_date + relativedelta(days=11))
        self._extract_date("today plus 10 months",
                      self.ref_date + relativedelta(months=10))
        self._extract_date("today plus 10 years",
                      self.ref_date + relativedelta(years=10))
        self._extract_date("today plus 10 years, 10 months and 1 day",
                      self.ref_date + relativedelta(
                            days=1, months=10, years=10))
        self._extract_date("tomorrow + 10 days",
                      self.ref_date + relativedelta(days=11))
        
    # # TODO "minus 10" converts to "-10" 
    # def test_extract_date_minus(self):

    #     self._extract_date("now minus 10 days",
    #                     self.now - relativedelta(days=10))
    #     self._extract_date("today minus 10 days",
    #                     self.ref_date - relativedelta(days=10))
    #     # TODO fix me
    #     # self._extract_date("today - 10 days",
    #     #           self.ref_date - relativedelta(days=10))
    #     # self._extract_date("yesterday - 10 days",
    #     #           self.ref_date - relativedelta(days=11))
    #     # self._extract_date("today - 10 years",
    #     #            self.ref_date.replace(year=self.ref_date.year - 10))

    #     self._extract_date("tomorrow minus 10 days",
    #                     self.ref_date - relativedelta(days=9))
    #     self._extract_date("today minus 10 months",
    #                     self.ref_date - relativedelta(months=10))
    #     self._extract_date("today minus 10 years, 10 months and 1 day",
    #                     self.ref_date - relativedelta(days=1, months=10,
    #                                                   years=10))

    def test_extract_date_timedelta_fallback(self):

        self._extract_date("now plus 10 months",
                        self.now + relativedelta(months=10))
        self._extract_date("today plus 10.5 months",
                        self.ref_date + timedelta(days=10.5 * DAYS_IN_1_MONTH))
        self._extract_date("now plus 10 years",
                        self.now + relativedelta(years=10))
        self._extract_date("today plus 10.5 years",
                      self.ref_date + timedelta(days=10.5 * DAYS_IN_1_YEAR))
        
    def test_extract_date_before(self):

        self._extract_date("before today",
                      self.ref_date - relativedelta(days=1))
        self._extract_date("before tomorrow", self.ref_date)
        self._extract_date("before yesterday",
                      self.ref_date - relativedelta(days=2))
        self._extract_date("before march 12",
                      self.ref_date.replace(month=3, day=11))
        self._extract_date("before march 12 next year",
                           date(year=2118, month=3, day=11))

        self._extract_date("before 1992", date(year=1991, month=12, day=31))
        self._extract_date("before 1992", date(year=1991, day=1, month=1),
                      DateTimeResolution.YEAR)
        self._extract_date("before 1992", date(year=1990, day=1, month=1),
                      DateTimeResolution.DECADE)
        self._extract_date("before 1992", date(year=1900, day=1, month=1),
                      DateTimeResolution.CENTURY)

        self._extract_date("before april",
                      date(month=3, day=31, year=self.ref_date.year))
        self._extract_date("before april",
                      date(month=1, day=1, year=self.ref_date.year),
                      DateTimeResolution.YEAR)
        self._extract_date("before april",
                      date(month=1, day=1, year=2110),
                      DateTimeResolution.DECADE)

        self._extract_date("before april 1992",
                      date(month=3, day=31, year=1992))
        self._extract_date("before april 1992",
                      date(month=1, day=1, year=1992),
                      DateTimeResolution.YEAR)
        self._extract_date("before april 1992",
                      date(month=1, day=1, year=1990),
                      DateTimeResolution.DECADE)
        
        self._extract_date("2 years before present",
                      self.ref_date - relativedelta(years=2))
        # self._extract_date("556 before present",
        #               self.ref_date - relativedelta(years=556))
        # self._extract_date("march 1st 556 before present",
        #               date(day=1, month=3,
        #                    year=self.ref_date.year - 556))
        self._extract_date("10th day of the 1st year before present",
                      date(day=10, month=1, year=self.ref_date.year-1))
        self._extract_date("364th day before present",
                      self.ref_date - timedelta(days=364))
        self._extract_date("364th month before present",
                      self.ref_date - relativedelta(months=364))
        self._extract_date("364th week before present",
                      self.ref_date - timedelta(weeks=364))
        self._extract_date("3rd century before present",
                      self.ref_date - relativedelta(years=300))
        self._extract_date("11th decade before present",
                      self.ref_date - relativedelta(years=110))
        self._extract_date("1st millennium before present",
                      self.ref_date - relativedelta(years=1000))
        
    def test_extract_date_after(self):

        self._extract_date("after today",
                      self.ref_date + relativedelta(days=1))
        self._extract_date("after yesterday", self.ref_date)
        self._extract_date("after tomorrow",
                      self.ref_date + relativedelta(days=2))

        self._extract_date("after today",
                      self.ref_date.replace(day=8),
                      DateTimeResolution.WEEK)
        self._extract_date("after today",
                      date(day=1, month=self.ref_date.month + 1,
                           year=self.ref_date.year),
                      DateTimeResolution.MONTH)
        self._extract_date("after tomorrow",
                      date(day=1, month=1, year=2120),
                      DateTimeResolution.DECADE)

        self._extract_date("after march 12",
                      self.ref_date.replace(month=3, day=12) +
                      relativedelta(days=1))

        self._extract_date("after 1992", date(year=1993, day=1, month=1))
        self._extract_date("after 1992", date(year=1993, day=4, month=1),
                      DateTimeResolution.WEEK)
        self._extract_date("after 1992", date(year=1993, day=1, month=1),
                      DateTimeResolution.MONTH)
        self._extract_date("after 1992", date(year=1993, day=1, month=1),
                      DateTimeResolution.YEAR)
        self._extract_date("after 1992", date(year=2000, day=1, month=1),
                      DateTimeResolution.DECADE)
        self._extract_date("after 1992", date(year=2000, day=1, month=1),
                      DateTimeResolution.CENTURY)
        self._extract_date("after 1992", date(year=2000, day=1, month=1),
                      DateTimeResolution.MILLENNIUM)

        self._extract_date("after april",
                      date(day=1, month=5, year=self.ref_date.year))
        self._extract_date("after april",
                      date(year=self.ref_date.year, day=3, month=5),
                      DateTimeResolution.WEEK)
        self._extract_date("after april",
                      date(year=self.ref_date.year, day=1, month=5),
                      DateTimeResolution.MONTH)
        self._extract_date("after april", date(year=2120, day=1, month=1),
                      DateTimeResolution.DECADE)

        self._extract_date("after april 1992", date(year=1992, day=1, month=5),
                      DateTimeResolution.MONTH)
        self._extract_date("after april 1992", date(year=1993, day=1, month=1),
                      DateTimeResolution.YEAR)
        self._extract_date("after april 1992", date(year=2000, day=1, month=1),
                      DateTimeResolution.CENTURY)

        self._extract_date("after 2600", date(year=2601, day=1, month=1))
        self._extract_date("after 2600", date(year=2601, day=1, month=1),
                      DateTimeResolution.MONTH)
        self._extract_date("after 2600", date(year=2601, day=1, month=1),
                      DateTimeResolution.YEAR)

        self._extract_date("after 2600", date(year=2610, day=1, month=1),
                      DateTimeResolution.DECADE)
        self._extract_date("after 2600", date(year=2700, day=1, month=1),
                      DateTimeResolution.CENTURY)
        
    def test_extract_date_this(self):

        _current_century = ((self.ref_date.year // 100) - 1) * 100
        _current_decade = (self.ref_date.year // 10) * 10

        self._extract_date("this month", self.ref_date.replace(day=1))
        self._extract_date("this week", self.ref_date - relativedelta(
            days=self.ref_date.weekday()))
        self._extract_date("this year", self.ref_date.replace(day=1, month=1))
        self._extract_date("current year", self.ref_date.replace(day=1, month=1))
        self._extract_date("present day", self.ref_date)
        self._extract_date("current decade", date(day=1, month=1, year=2110))
        self._extract_date("current century", date(day=1, month=1, year=2100))
        self._extract_date("this millennium", date(day=1, month=1, year=2000))
        
    def test_extract_date_next(self):

        self._extract_date("next month",
                      (self.ref_date + relativedelta(
                            days=DAYS_IN_1_MONTH)).replace(day=1))
        self._extract_date("next week",
                      get_week_range(self.ref_date + relativedelta(weeks=1))[
                          0])
        self._extract_date("next century",
                      date(year=2200, day=1, month=1))
        self._extract_date("next year",
                      date(year=self.ref_date.year + 1, day=1, month=1))
        
    def test_extract_date_last(self):

        self._extract_date("last month",
                        (self.ref_date - relativedelta(
                            days=DAYS_IN_1_MONTH)).replace(day=1))
        self._extract_date("last week",
                        get_week_range(self.ref_date - relativedelta(weeks=1))[
                            0])
        self._extract_date("last year", date(year=self.ref_date.year - 1,
                                        day=1,
                                        month=1))
        self._extract_date("last century", date(year=2000, day=1, month=1))

        self._extract_date("last day of the 10th century",
                      date(day=31, month=12, year=999))

        self._extract_date("last day of this month",
                      self.ref_date.replace(day=28))
        self._extract_date("last day of the month",
                      self.ref_date.replace(day=28))

        self._extract_date("last day of this year",
                      date(day=31, month=12, year=self.ref_date.year))
        self._extract_date("last day of the year",
                      date(day=31, month=12, year=self.ref_date.year))

        self._extract_date("last day of this century",
                      date(day=31, month=12, year=2199))
        self._extract_date("last day of the century",
                      date(day=31, month=12, year=2199))

        self._extract_date("last day of this decade",
                      date(day=31, month=12, year=2119))
        self._extract_date("last day of the decade",
                      date(day=31, month=12, year=2119))
        self._extract_date("last day of this millennium",
                      date(day=31, month=12, year=2999))
        self._extract_date("last day of the millennium",
                      date(day=31, month=12, year=2999))
        self._extract_date("last day of the 20th month of the 5th millennium",
                      date(year=4000, day=31, month=1) +
                      relativedelta(months=19))
        self._extract_date("last day of the 9th decade of the 5th millennium",
                      date(day=31, month=12, year=4089))
        self._extract_date("last day of the 10th millennium",
                      date(day=31, month=12, year=9999))
        
    def test_extract_date_first(self):

        self._extract_date("first day", self.ref_date.replace(day=1))
        self._extract_date("first day of this month",
                      self.ref_date.replace(day=1))
        self._extract_date("first day of this year",
                      self.ref_date.replace(day=1, month=1))
        self._extract_date("first day of this decade", date(day=1, month=1,
                                                       year=2110))
        self._extract_date("first day of this century", date(day=1, month=1,
                                                        year=2100))
        self._extract_date("first day of this millennium", date(day=1, month=1,
                                                           year=2000))

        self._extract_date("first month", self.ref_date.replace(day=1, month=1))

        self._extract_date("first decade", date(year=1, day=1, month=1))
        self._extract_date("first year", date(year=1, day=1, month=1))
        self._extract_date("first century", date(year=1, day=1, month=1))

        self._extract_date("first day of the 10th century",
                      date(day=1, month=1, year=900))

        self._extract_date("first day of the month",
                      self.ref_date.replace(day=1))
        self._extract_date("first day of the year",
                      date(day=1, month=1, year=self.ref_date.year))

        self._extract_date("first day of the century",
                      date(day=1, month=1, year=2100))
        self._extract_date("first day of the decade",
                      date(day=1, month=1, year=2110))
        self._extract_date("first day of the millennium",
                      date(day=1, month=1, year=2000))

        self._extract_date("first day of the 10th millennium",
                      date(day=1, month=1, year=9000))
        
    def test_extract_date_seasons(self):
        _ref_date = datetime(2022, 2, 3, 12, 0, tzinfo=timezone.utc)
        _ref_season = date_to_season(_ref_date)
        self.assertEqual(_ref_season, Season.WINTER)

        # TODO start/end of season/winter/summer/fall/spring...

        def _test_season(test_date, expected_date, season, hemi=Hemisphere.NORTH):
            self._extract_date(test_date, 
                               expected_date.date(),
                               anchor=_ref_date,
                               hemi=hemi)
            self.assertEqual(date_to_season(expected_date,
                                            hemisphere=hemi),
                             season)
        
        _test_season("this season",
                     datetime(2021, 12, 21, 15, 59, 18, tzinfo=timezone.utc),
                     _ref_season)
        _test_season("next season",
                     datetime(2022, 3, 20, 15, 33, 25, tzinfo=timezone.utc),
                     Season.SPRING)
        _test_season("last season",
                     datetime(2021, 9, 22, 19, 21, 6, tzinfo=timezone.utc),
                     Season.FALL)

        # test named season in {hemisphere}
        _test_season("this spring in north hemisphere",
                     datetime(2022, 3, 20, 15, 33, 25, tzinfo=timezone.utc),
                     Season.SPRING)
        _test_season("this spring in northern hemisphere",
                     datetime(2022, 3, 20, 15, 33, 25, tzinfo=timezone.utc),
                     Season.SPRING)

        _test_season("this spring in south hemisphere",
                     datetime(2022, 9, 23, 1, 3, 42, tzinfo=timezone.utc),
                     Season.SPRING,
                     Hemisphere.SOUTH)
        _test_season("this spring in southern hemisphere",
                     datetime(2022, 9, 23, 1, 3, 42, tzinfo=timezone.utc),
                     Season.SPRING,
                     Hemisphere.SOUTH)
        
        try:
            import simple_NER

            # test named season in {country}
            _test_season("this spring in Portugal",
                         datetime(2022, 3, 20, 15, 33, 25, tzinfo=timezone.utc),
                         Season.SPRING)
            _test_season("last spring in Portugal",
                         datetime(2021, 3, 20, 9, 37, 29, tzinfo=timezone.utc),
                         Season.SPRING)
            _test_season("next winter in Portugal",
                         datetime(2022, 12, 21, 21, 48, 13, tzinfo=timezone.utc),
                         Season.WINTER)

            _test_season("this spring in Brazil",
                         datetime(2021, 9, 22, 19, 21, 6, tzinfo=timezone.utc),
                         Season.SPRING,
                         Hemisphere.SOUTH)
            _test_season("next winter in Brazil",
                         datetime(2022, 6, 21, 9, 13, 51, tzinfo=timezone.utc),
                         Season.WINTER,
                         Hemisphere.SOUTH)

            # test named season in {capital city}
            _test_season("this spring in Lisbon",
                         datetime(2022, 3, 20, 15, 33, 25, tzinfo=timezone.utc),
                         Season.SPRING)
            _test_season("this spring in Canberra",
                         datetime(2022, 9, 23, 1, 3, 42, tzinfo=timezone.utc),
                         Season.SPRING,
                         Hemisphere.SOUTH)

        except ImportError:
            print("Could not test location tagging")
        
        # test named season
        _test_season("winter is coming",
                     datetime(2022, 12, 21, 21, 48, 13, tzinfo=timezone.utc),
                     Season.WINTER)

        _test_season("spring",
                     datetime(2022, 3, 20, 15, 33, 25, tzinfo=timezone.utc),
                     Season.SPRING)
        # forced meterological season (bc year)
        _test_season("spring of 1991",
                     datetime(day=1, month=3, year=1991),
                     Season.SPRING)
        _test_season("summer of 1969",
                     datetime(day=1, month=12, year=1969),
                     Season.SUMMER,
                     Hemisphere.SOUTH)

        _test_season("this spring",
                     datetime(2022, 3, 20, 15, 33, 25, tzinfo=timezone.utc),
                     Season.SPRING)
        _test_season("this spring",
                     datetime(2022, 9, 23, 1, 3, 42, tzinfo=timezone.utc),
                     Season.SPRING,
                     Hemisphere.SOUTH)

        _test_season("next spring",
                     datetime(2022, 3, 20, 15, 33, 25, tzinfo=timezone.utc),
                     Season.SPRING)
        _test_season("next spring",
                     datetime(2022, 9, 23, 1, 3, 42, tzinfo=timezone.utc),
                     Season.SPRING,
                     Hemisphere.SOUTH)

        _test_season("last spring",
                     datetime(2021, 3, 20, 9, 37, 29, tzinfo=timezone.utc),
                     Season.SPRING)
        _test_season("last spring",
                     datetime(2021, 9, 22, 19, 21, 6, tzinfo=timezone.utc),
                     Season.SPRING,
                     Hemisphere.SOUTH)

        _test_season("this summer",
                     datetime(2022, 6, 21, 9, 13, 51, tzinfo=timezone.utc),
                     Season.SUMMER)
        _test_season("next summer",
                     datetime(2022, 6, 21, 9, 13, 51, tzinfo=timezone.utc),
                     Season.SUMMER)
        _test_season("last summer",
                     datetime(2021, 6, 21, 3, 32, 10, tzinfo=timezone.utc),
                     Season.SUMMER)

        _test_season("this fall",
                     datetime(2022, 9, 23, 1, 3, 42, tzinfo=timezone.utc),
                     Season.FALL)
        _test_season("next fall",
                     datetime(2022, 9, 23, 1, 3, 42, tzinfo=timezone.utc),
                     Season.FALL)
        _test_season("last autumn",
                     datetime(2021, 9, 22, 19, 21, 6, tzinfo=timezone.utc),
                     Season.FALL)

        # fails 2027 (2027-03-20; shifting equinox)
        self._extract_date("winter",
                           datetime(now_local().year-1, 12, 22, 0, 0, tzinfo=timezone.utc),
                           anchor=datetime(now_local().year, 2, 3, 12, 0, tzinfo=timezone.utc))
        # NOTE: those differ because when asked in the season (local time) it will return the start
        # of the season, otherwise "winter of 69" would return an 68 date
        _test_season("this winter",
                     datetime(2022, 12, 21, 21, 48, 13, tzinfo=timezone.utc),
                     Season.WINTER)
        
        _test_season("next winter",
                     datetime(2022, 12, 21, 21, 48, 13, tzinfo=timezone.utc),
                     Season.WINTER)
        _test_season("last winter",
                     datetime(2020, 12, 21, 10, 2, 20, tzinfo=timezone.utc),
                     Season.WINTER)
        
    def test_extract_date_weekends(self):
        # TODO plus / minus / after N weekends
        # TODO N weekends ago
        saturday, sunday = get_weekend_range(self.ref_date)
        assert saturday.weekday() == 5
        assert sunday.weekday() == 6
        
        self._extract_date("this weekend", saturday)
        self._extract_date("next weekend", saturday)
        self._extract_date("last weekend", saturday - relativedelta(days=7))

        self._extract_date("this weekend", saturday,
                      anchor=saturday)
        self._extract_date("this weekend", saturday,
                      anchor=sunday)
        self._extract_date("next weekend", saturday + relativedelta(days=7),
                      anchor=saturday)
        self._extract_date("next weekend", saturday + relativedelta(days=7),
                      anchor=sunday)
        self._extract_date("last weekend", saturday - relativedelta(days=7),
                      anchor=saturday)
        self._extract_date("last weekend", saturday - relativedelta(days=7),
                      anchor=sunday)
        
    def test_extract_date_is(self):

        self._extract_date("the year is 2100", date(year=2100, month=1, day=1))
        self._extract_date("the year was 1969", date(year=1969, month=1, day=1))
        self._extract_date("the day is 2", self.ref_date.replace(day=2))
        self._extract_date("the month is 8",
                      self.ref_date.replace(month=8, day=1))

        self._extract_date("this is the second day of the third "
                      "month of the first year of the 9th millennium,",
                      datetime(day=2, month=3, year=8000))
        self._extract_date("this is the second day of the third "
                      "month of the 9th millennium,",
                      datetime(day=2, month=3, year=8000))
        
    def test_extract_date_of(self):

        self._extract_date("first day of the first millennium",
                      datetime(day=1, month=1, year=1))
        self._extract_date("first day of the first century",
                      datetime(day=1, month=1, year=1))
        self._extract_date("first day of the first decade",
                      datetime(day=1, month=1, year=1))
        self._extract_date("first day of the first year",
                      datetime(day=1, month=1, year=1))

        self._extract_date("first day of the first week",
                      datetime(day=4, month=1, year=self.ref_date.year))

        self._extract_date("3rd day",
                      self.ref_date.replace(day=3))
        self._extract_date("3rd day of may",
                      self.ref_date.replace(day=3, month=5))
        self._extract_date("3rd day of the 5th century",
                      datetime(day=3, month=1, year=400))
        self._extract_date("3rd day of the 5th month of the 10th century",
                      datetime(day=3, month=5, year=900))
        self._extract_date("25th month of the 10th century",
                      datetime(day=1, month=1, year=902))
        self._extract_date("3rd day of the 25th month of the 10th century",
                      datetime(day=3, month=1, year=902))
        self._extract_date("3rd day of 1973",
                      datetime(day=3, month=1, year=1973))
        self._extract_date("3rd day of the 17th decade",
                      datetime(day=3, month=1, year=160))
        self._extract_date("3rd day of the 10th millennium",
                      datetime(day=3, month=1, year=9000))
        self._extract_date("301st day of the 10th century",
                      datetime(day=28, month=10, year=900))
        self._extract_date("first century of the 6th millennium",
                      datetime(day=1, month=1, year=5000))
        self._extract_date("first decade of the 6th millennium",
                      datetime(day=1, month=1, year=5000))
        self._extract_date("39th decade of the 6th millennium",
                      datetime(day=1, month=1, year=5380))
        self._extract_date("the 20th year of the 6th millennium",
                      datetime(day=1, month=1, year=5019))
        self._extract_date("the 20th day of the 6th millennium",
                      datetime(day=20, month=1, year=5000))
        self._extract_date("last day of the 39th decade of the 6th millennium",
                      datetime(day=31, month=12, year=5389))
        
    def test_extract_date_months(self):

        self._extract_date("january", self.ref_date.replace(day=1, month=1))
        self._extract_date("last january", self.ref_date.replace(day=1, month=1))
        self._extract_date("next january", date(day=1, month=1,
                                           year=self.ref_date.year + 1))

        self._extract_date("in 29 november", date(day=29, month=11,
                                             year=self.ref_date.year))
        self._extract_date("last november 27", date(day=27, month=11,
                                               year=self.ref_date.year - 1))
        self._extract_date("next 3 november", date(day=3, month=11,
                                              year=self.ref_date.year))
        self._extract_date("last 3 november 1872",
                      date(day=3, month=11, year=1872))
        
    def test_extract_date_weeks(self):

        def _test_week(date_str, expected_date, anchor=self.ref_date):
            extracted = self.tagger.extract_date(date_str, anchor)
            if isinstance(expected_date, datetime):
                expected_date = expected_date.date()
            
            if extracted is None:
                self.assertEqual(extracted, expected_date)
            else:
                self.assertEqual(extracted.value, expected_date)
                # NOTE: weeks start on sunday
                # TODO start on thursdays?
                self.assertEqual(extracted.value.weekday(), 0)
            

        _test_week("this week", self.ref_date.replace(day=1))
        _test_week("next week", self.ref_date.replace(day=8))
        _test_week("last week", self.ref_date.replace(day=25, month=1))
        _test_week("first week", self.ref_date.replace(day=4, month=1))

        # test Nth week
        self.assertRaises(ValueError, self.tagger.extract_date,
                          "5th week of this month", now_local())

        # test week of month  -  day=1 in week
        assert self.ref_date.replace(day=1).weekday() == 0
        _test_week("first week of this month",
                   self.ref_date.replace(day=1))
        _test_week("second week of this month",
                   self.ref_date.replace(day=8, month=2))
        _test_week("3rd week of this month",
                   self.ref_date.replace(day=15, month=2))
        _test_week("4th week of this month",
                   self.ref_date.replace(day=22, month=2))

        # test week of month - month day=1 not in week (weeks start on sundays)
        _anchor = datetime(day=1, month=2, year=1991, tzinfo=timezone.utc)
        assert _anchor.replace(day=1).weekday() != 0

        _test_week("first week of this month",
                   _anchor.replace(day=4), anchor=_anchor)
        _test_week("second week of this month",
                   _anchor.replace(day=11), anchor=_anchor)
        _test_week("3rd week of this month",
                   _anchor.replace(day=18), anchor=_anchor)
        _test_week("4th week of this month",
                   _anchor.replace(day=25), anchor=_anchor)

        # test week of year
        _test_week("first week of this year",
                   self.ref_date.replace(day=4, month=1))
        _test_week("2nd week of this year",
                   self.ref_date.replace(day=11, month=1))
        _test_week("3rd week of this year",
                   self.ref_date.replace(day=18, month=1))
        _test_week("10th week of this year",
                   self.ref_date.replace(day=8, month=3))

        # test week of decade
        _test_week("first week of this decade",
                   date(day=6, month=1, year=2110))
        _test_week("2nd week of this decade",
                   date(day=13, month=1, year=2110))
        _test_week("third week of this decade",
                   date(day=20, month=1, year=2110))
        _test_week("hundredth week of this decade",
                   date(day=30, month=11, year=2111))

        # test week of century
        _test_week("first week of this century",
                   date(day=4, month=1, year=2100))
        _test_week("2nd week of this century",
                   date(day=11, month=1, year=2100))
        _test_week("3rd week of this century",
                   date(day=18, month=1, year=2100))
        _test_week("thousandth week of this century",
                   date(day=27, month=2, year=2119))

        # test week of millennium
        _test_week("first week of this millennium",
                   date(day=3, month=1, year=2000))
        _test_week("2nd week of this millennium",
                   date(day=10, month=1, year=2000))
        _test_week("3rd week of this millennium",
                   date(day=17, month=1, year=2000))
        _test_week("ten thousandth week of this millennium",
                   date(day=22, month=8, year=2191))

        # test last week
        _test_week("last week of this month",
                   self.ref_date.replace(day=22))
        _test_week("last week of this year",
                   self.ref_date.replace(day=27, month=12))
        _test_week("last week of this decade",
                   date(day=25, month=12, year=2119))
        _test_week("last week of this century",
                   date(day=30, month=12, year=2199))
        _test_week("last week of this millennium",
                   date(day=30, month=12, year=2999))
        
    def test_extract_date_years(self):
        _anchor = datetime(day=10, month=5, year=2020, tzinfo=timezone.utc)

        # test explicit year (of YYYY)
        self._extract_date("january of 90",
                      date(day=1, month=1, year=1990),
                      anchor=_anchor)
        self._extract_date("january of 69",
                      date(day=1, month=1, year=1969),
                      anchor=_anchor)
        self._extract_date("january 69",
                      date(day=1, month=1, year=1969),
                      anchor=_anchor)
        self._extract_date("january of 19",
                      date(day=1, month=1, year=2019),
                      anchor=_anchor)
        self._extract_date("january of 09",
                      date(day=1, month=1, year=2009),
                      anchor=_anchor)

        # test implicit years, "the 90s", "the 900s"
        self._extract_date("the 70s",
                      _anchor.replace(year=1970),
                      anchor=_anchor)
        self._extract_date("the 600s",
                      _anchor.replace(year=600),
                      anchor=_anchor)

        # test greedy flag - standalone numbers are years
        self._extract_date("1992",
                      _anchor.replace(year=1992),
                      anchor=_anchor,
                      greedy=True)
        self._extract_date("1992", None, anchor=_anchor)

        self._extract_date("992",
                      _anchor.replace(year=992),
                      anchor=_anchor,
                      greedy=True)
        self._extract_date("992", None, anchor=_anchor)

        self._extract_date("132",
                      _anchor.replace(year=132),
                      anchor=_anchor,
                      greedy=True)
        self._extract_date("132", None, anchor=_anchor)

        self._extract_date("79",
                      _anchor.replace(year=1979),
                      anchor=_anchor,
                      greedy=True)
        self._extract_date("79", None, anchor=_anchor)

        self._extract_date("13",
                      _anchor.replace(year=2013),
                      anchor=_anchor,
                      greedy=True)
        self._extract_date("13", None, anchor=_anchor)

        self._extract_date("01",
                      _anchor.replace(year=2001),
                      anchor=_anchor,
                      greedy=True)
        self._extract_date("0",
                      _anchor.replace(year=2000),
                      anchor=_anchor,
                      greedy=True)
        self._extract_date("9", None, anchor=_anchor)

    def test_extract_date_named_dates(self):
        _anchor = datetime(day=10, month=5, year=2020)

        self._extract_date("christmas eve",
                           date(day=24, month=12, year=2020), anchor=_anchor)
        self._extract_date("this christmas",
                           date(day=25, month=12, year=2020), anchor=_anchor)
        self._extract_date("last christmas",
                           date(day=25, month=12, year=2019), anchor=_anchor)
        self._extract_date("next christmas",
                           date(day=25, month=12, year=2020), anchor=_anchor)
        
        # variable dates
        self._extract_date("this easter",
                           date(day=12, month=4, year=2020), anchor=_anchor)
        self._extract_date("easter next year",
                            date(day=4, month=4, year=2021), anchor=_anchor)
        self._extract_date("next easter",
                           date(day=4, month=4, year=2021), anchor=_anchor)
        self._extract_date("easter 1 year ago",
                           date(day=21, month=4, year=2019), anchor=_anchor)
        # based on easter
        self._extract_datetime("one day before pentecost next year at 3 pm",
                               datetime(day=22, month=5, year=2021, hour=15),
                               anchor=_anchor)

        # test location based holidays
        self._extract_date("independence day",
                      date(day=4, month=7, year=2020), anchor=_anchor)
        self._extract_date("Restauração da Independência", None)
        self._extract_date("independence day",
                      date(day=4, month=7, year=2020), anchor=_anchor)

        _anchor = datetime(day=31, month=12, year=2020)

        self._extract_date("this christmas",
                      date(day=25, month=12, year=2020), anchor=_anchor)
        self._extract_date("last christmas",
                      date(day=25, month=12, year=2020), anchor=_anchor)
        self._extract_date("next christmas",
                      date(day=25, month=12, year=2021), anchor=_anchor)
    
    def test_extract_date_named_eras(self):
         # test {Nth X} of {era}
        self._extract_date("20th day of the common era",
                      date(day=20, month=1, year=1))
        self._extract_date("20th month of the common era",
                      date(day=1, month=8, year=2))
        self._extract_date("20th year of the common era",
                      date(day=1, month=1, year=20))
        self._extract_date("20th decade of the common era",
                      date(day=1, month=1, year=190))
        self._extract_date("21th century of the common era",
                      date(day=1, month=1, year=2000))
        self._extract_date("2nd millennium of the common era",
                      date(day=1, month=1, year=1000))

        # test {date} of {era}
        self._extract_date("20 may 1992 anno domini",
                      date(day=20, month=5, year=1992))

        # test {year} of {era}
        self._extract_date("1992 christian era",
                      date(day=1, month=1, year=1992))

        # test ambiguous year
        self._extract_date("1 january christian era",
                      date(day=1, month=1, year=1))
    
        
if __name__ == '__main__':
    unittest.main() # pragma: no cover