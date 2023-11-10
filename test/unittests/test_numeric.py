import unittest

from ovos_classifiers.heuristics.numeric import EnglishNumberParser
from ovos_classifiers.heuristics.tokenize import word_tokenize


class TestEnglish(unittest.TestCase):

    def test_convert(self):

        parser = EnglishNumberParser()

        tokens = parser.convert_words_to_numbers("this is test number two")
        sp1, sp2, _ = word_tokenize("this is test number two", spans=True)[4]
        original_span = (sp1, sp2)
        self.assertEqual(tokens.text, "this is test number 2")
        self.assertEqual(tokens.word_list, ["this", "is", "test", "number", "2"])
        num_token = tokens[4]
        self.assertTrue(num_token.isNumeric)
        self.assertTrue(num_token.isDigit)
        self.assertFalse(num_token.isOrdinal)
        self.assertEqual(num_token.word, "2")
        self.assertEqual(num_token.number, 2)
        self.assertEqual(num_token.original, "two")
        self.assertEqual(num_token.spanned_original, (num_token.original, original_span))  # ("two", (20, 23))

        # fractional
        tokens = parser.convert_words_to_numbers("this is test number two and a half")
        spans = word_tokenize("this is test number two and a half", spans=True)
        original_span = (spans[4][0], spans[7][1])
        self.assertEqual(tokens.text, "this is test number 2.5")
        self.assertEqual(tokens.word_list, ["this", "is", "test", "number", "2.5"])
        num_token = tokens[4]
        self.assertTrue(num_token.isNumeric)
        self.assertFalse(num_token.isDigit)
        self.assertFalse(num_token.isOrdinal)
        self.assertEqual(num_token.word, "2.5")
        self.assertEqual(num_token.number, 2.5)
        self.assertEqual(num_token.original, "two and a half")
        self.assertEqual(num_token.spanned_original, (num_token.original, original_span))  # ('two and a half', (20, 34))

        # unconverted ordinal
        tokens = parser.convert_words_to_numbers("this is the first test")
        sp1, sp2, _ = word_tokenize("this is the first test", spans=True)[3]
        original_span = (sp1, sp2)
        self.assertEqual(tokens.text, "this is the first test")
        self.assertEqual(tokens.word_list, ["this", "is", "the", "first", "test"])
        num_token = tokens[3]
        self.assertTrue(num_token.isOrdinal)
        self.assertFalse(num_token.isNumeric)
        self.assertFalse(num_token.isDigit)
        self.assertEqual(num_token.word, "first")
        self.assertEqual(num_token.number, 1)
        self.assertEqual(num_token.original, "first")
        self.assertEqual(num_token.spanned_original, ("first", original_span))

        # converted ordinal
        tokens = parser.convert_words_to_numbers("this is the first test", ordinals=True)
        self.assertEqual(tokens.text, "this is the 1st test")
        self.assertEqual(tokens.word_list, ["this", "is", "the", "1st", "test"])
        num_token = tokens[3]
        self.assertTrue(num_token.isOrdinal)
        self.assertFalse(num_token.isNumeric)
        self.assertFalse(num_token.isDigit)
        self.assertEqual(num_token.word, "1st")
        self.assertEqual(num_token.number, 1)
        self.assertEqual(num_token.original, "first")
        self.assertEqual(num_token.spanned_original, ("first", original_span))
        
        self.assertEqual(parser.convert_words_to_numbers("this is the 2/3 test").text,
                         f"this is the {2/3} test")

    def test_numbers(self):
        parser = EnglishNumberParser()

        def test_xtract(utt, expected_numbers,
                             ordinals=False,
                             fractions=True,
                             short_scale=True):
            # extract_numbers
            numbers = [n.value for n in parser.extract_numbers(utt,
                                                               ordinals=ordinals,
                                                               fractions=fractions,
                                                               short_scale=short_scale)]            
            if not isinstance(expected_numbers, list):
                expected_numbers = [expected_numbers]
            self.assertEqual(numbers, expected_numbers)

        test_xtract("this is test number two", 2)
        test_xtract("this is test number two and a half", 2.5)
        test_xtract("this is the first test", [])
        test_xtract("this is the first test", 1, ordinals=True)
        test_xtract("this is test number one 2 three", [1, 2, 3])

        test_xtract("this is a one two three  test", [1.0, 2.0, 3.0])
        test_xtract("it's  a four five six  test", [4.0, 5.0, 6.0])
        test_xtract("this is a ten eleven twelve  test", [10.0, 11.0, 12.0])
        test_xtract("this is a one twenty one  test", [1.0, 21.0])
        test_xtract("1 dog, seven pigs, macdonald had a farm, 3 times 5 macarena", [1, 7, 3, 5])
        test_xtract("two beers for two bears", [2.0, 2.0])
        test_xtract("twenty 20 twenty", [20, 20, 20])
        test_xtract("twenty 20 22", [20.0, 20.0, 22.0])
        test_xtract("twenty twenty two twenty", [20, 22, 20])
        test_xtract("twenty 2", 22.0)
        test_xtract("twenty 20 twenty 2", [20, 20, 22])
        test_xtract("third one", [])
        test_xtract("third one", 3, ordinals=True)
        test_xtract("a third one", [])
        test_xtract("a third one", 3, ordinals=True)
        test_xtract("half an hour", 0.5)
        test_xtract("one third one", [1 / 3, 1])
        test_xtract("six trillion", [6e12], short_scale=True)
        test_xtract("six trillion", [6e18], short_scale=False)
        test_xtract("two pigs and six trillion bacteria", [2, 6e12], short_scale=True)
        test_xtract("two pigs and six trillion bacteria", [2, 6e18], short_scale=False)
        test_xtract("thirty second or first", [32, 1], ordinals=True)
        test_xtract("this is a seven eight nine and a half test", [7.0, 8.0, 9.5])

        test_xtract("grobo 0", 0)
        test_xtract("a couple of beers", 2)
        test_xtract("a couple hundred beers", 200)
        test_xtract("a couple thousand beers", 2000)
        test_xtract("totally 100%", 100)

        test_xtract("this is 2 test", 2)
        test_xtract("this is test number 4", 4)
        test_xtract("three cups", 3)
        test_xtract("1/3 cups", 1.0 / 3.0)
        test_xtract("quarter cup", 0.25)
        test_xtract("1/4 cup", 0.25)
        test_xtract("one fourth cup", 0.25)
        test_xtract("2/3 cups", 2.0 / 3.0)
        test_xtract("3/4 cups", 3.0 / 4.0)
        test_xtract("1 and 3/4 cups", 1.75)
        test_xtract("1 and a half cups", 1.5)
        test_xtract("one cup and a half (tomato)", [1, 0.5])
        test_xtract("one and two halves", 2)
        test_xtract("three quarter cups", [3, 0.25])
        test_xtract("three quarter cups", 3, fractions=False)
        test_xtract("three quarters", 3.0 / 4.0)
        test_xtract("twenty two", 22)
        test_xtract("Twenty two with a leading capital letter", 22)
        test_xtract("twenty Two with Two capital letters", [22, 2])
        test_xtract("twenty Two with mixed capital letters", 22)
        test_xtract("two hundred", 200)
        test_xtract("two hundredth", 200, ordinals=True)
        test_xtract("two hundredth", [])
        test_xtract("two hundredths", 2/100)
        test_xtract("nine thousand", 9000)
        test_xtract("six hundred sixty six", 666)
        test_xtract("two million", 2000000)
        test_xtract("two million five hundred thousand tons of spinning metal", 2500000)
        test_xtract("six trillion", 6000000000000.0)
        test_xtract("six trillion", 6e+18, short_scale=False)
        test_xtract("one point five", 1.5)
        test_xtract("point five", 0.5)
        test_xtract("three dot fourteen", 3.14)
        test_xtract("zero point two", 0.2)
        test_xtract("hundreds of thousands", [100, 1000])
        test_xtract("billions of years older", 1000000000.0)
        test_xtract("billions of years older", 1000000000000.0, short_scale=False)
        test_xtract("one hundred thousand", 100000)
        test_xtract("minus 2", -2)
        test_xtract("negative seventy", -70)
        test_xtract("thousand million", 1000000000)

        # suppress fractional and ordinal
        test_xtract("for the hundredth time, i said two not two thirds", 2, fractions=False)

        # Verify non-power multiples of ten no longer discard
        # adjacent multipliers
        test_xtract("twenty thousand", 20000)
        test_xtract("fifty million", 50000000)

        # Verify smaller powers of ten no longer cause miscalculation of larger
        # powers of ten (see MycroftAI#86)
        test_xtract("twenty billion three hundred million \
                                        nine hundred fifty thousand six hundred \
                                        seventy five point eight", 20300950675.8)
        test_xtract("nine hundred ninety nine million nine \
                                        hundred ninety nine thousand nine \
                                        hundred ninety nine point nine", 999999999.9)

        test_xtract("eight hundred trillion two hundred fifty seven", 800000000000257.0)

        # sanity check
        test_xtract("third", 3, ordinals=True)
        test_xtract("sixth", 6, ordinals=True)

        # test explicit ordinals
        test_xtract("this is the 1st", 1, ordinals=True)
        test_xtract("this is the 2nd", 2, ordinals=True)
        test_xtract("this is the 3rd", 3, ordinals=True)
        test_xtract("this is the 4th", 4, ordinals=True)
        test_xtract("this is the 7th test", 7, ordinals=True)
        test_xtract("this is the 31st test", 31, ordinals=True)
        test_xtract("this is the 1st test", [])
        test_xtract("this is the 2nd test", [])
        test_xtract("this is the 3rd test", [])
        

        # test non ambiguous ordinals
        test_xtract("this is the first test", 1, ordinals=True)
        # test ambiguous ordinal/time unit
        test_xtract("this is a second test", 2, ordinals=True)
        test_xtract("remind me in a second", 2, ordinals=True)  # impossible to disambiguate 
        test_xtract("remind me in a second", [])
        test_xtract("one second", 1)
        test_xtract("one second", 1, ordinals=True)
        test_xtract("thirty five seconds", 35)
        test_xtract("thirty five seconds", 35, ordinals=True)
        test_xtract("half a second", 0.5)
        test_xtract("half a second", 0.5, ordinals=True)

        # test ambiguous ordinal/fractional
        test_xtract("this is the third test", 3.0, ordinals=True)
        # NOTE: this is no fractional
        # test_xtract("this is the third test", 1.0 / 3.0)

        test_xtract("one third of a cup", 1.0 / 3.0)

        # test big numbers / short vs long scale
        test_xtract("this is the billionth test", 1e09, ordinals=True)
        test_xtract("this is the billionth test", [])
        test_xtract("this is the billionth test", 1e12, ordinals=True, short_scale=False)
        test_xtract("this is the billionth test", [], short_scale=False)

        # test the Nth one
        test_xtract("the fourth one", 4.0, ordinals=True)
        test_xtract("the thirty sixth one", 36.0, ordinals=True)
        test_xtract("you are the second one", [])
        test_xtract("you are the second one", 2, ordinals=True)
        test_xtract("you are the 1st one", [])


    def test_number(self):
        parser = EnglishNumberParser()

        def _extract_number(utt, expected_number,
                             ordinals=False,
                             fractions=True,
                             short_scale=True):
            
            number = parser.extract_number(utt,
                                           ordinals=ordinals,
                                           fractions=fractions,
                                           short_scale=short_scale)
            
            val = number.value if number else None
            self.assertEqual(val, expected_number)

        # NOTE directly following (unrelated) whole numbers "twenty 22" will return the last number first
        # this is hard to tackle with the present code 

        _extract_number("this is test number one of two", 1)
        _extract_number("this is test number two and a half of three", 2.5)
        _extract_number("this is the first test of 2", 2)
        _extract_number("this is the first test of 2", 1, ordinals=True)
        
        _extract_number("1 dog, seven pigs, macdonald had a farm, 3 times 5 macarena", 1)
        _extract_number("twenty 2 times 2", 22)
        _extract_number("third one gone sixty", 60)
        _extract_number("third one gone sixty", 3, ordinals=True)
        _extract_number("half way to sixty", 60, fractions=False)
        _extract_number("a third one is six", 6)
        _extract_number("a third one is six", 3, ordinals=True)
        _extract_number("six trillion bacteria and two pigs", 6e12, short_scale=True)
        _extract_number("six trillion bacteria and two pigs", 6e18, short_scale=False)
        _extract_number("thirty second or first", 32, ordinals=True)
        _extract_number("for the hundredth time, i said two not two thirds", 2)
        _extract_number("for the hundredth time, i said two not two thirds", 100, ordinals=True)
        _extract_number("for the hundredth time, i said two thirds not two", 2/3)
        _extract_number("for the hundredth time, i said two thirds not two", 2, fractions=False)
        _extract_number("1st a couple of beers", 2)
        _extract_number("2nd couple hundred beers", 200)
        _extract_number("3rd a couple thousand beers", 2000)
        _extract_number("50% of 100", 50)
        _extract_number("minus 50 degree in two cities ", -50)
        _extract_number("point two of two", 0.2)
        _extract_number("three dot fourteen comes in 2 weeks", 3.14)
        _extract_number("nine hundred fifty thousand six hundred \
                         seventy five point eight or one", 950675.8)


if __name__ == "__main__":
    unittest.main()
