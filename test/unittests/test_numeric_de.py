import unittest

from ovos_classifiers.heuristics.numeric import GermanNumberParser
from ovos_classifiers.heuristics.tokenize import word_tokenize


class TestGerman(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = GermanNumberParser()

    def test_convert_tag(self):

        tokens = self.parser.convert_words_to_numbers("das ist test nummer zwei")
        sp1, sp2, _ = word_tokenize("das ist test nummer zwei", spans=True)[4]
        original_span = (sp1, sp2)
        self.assertEqual(tokens.text, "das ist test nummer 2")
        self.assertEqual(tokens.word_list, ["das", "ist", "test", "nummer", "2"])
        num_token = tokens[4]
        self.assertTrue(num_token.isNumeric)
        self.assertTrue(num_token.isDigit)
        self.assertFalse(num_token.isOrdinal)
        self.assertEqual(num_token.word, "2")
        self.assertEqual(num_token.number, 2)
        self.assertEqual(num_token.original, "zwei")
        self.assertEqual(num_token.spanned_original, (num_token.original, original_span))  # ("two", (20, 24))

        # fractional
        tokens = self.parser.convert_words_to_numbers("das ist test nummer zwei einhalb")
        spans = word_tokenize("das ist test nummer zwei einhalb", spans=True)
        original_span = (spans[4][0], spans[5][1])
        self.assertEqual(tokens.text, "das ist test nummer 2.5")
        self.assertEqual(tokens.word_list, ["das", "ist", "test", "nummer", "2.5"])
        num_token = tokens[4]
        self.assertTrue(num_token.isNumeric)
        self.assertFalse(num_token.isDigit)
        self.assertFalse(num_token.isOrdinal)
        self.assertEqual(num_token.word, "2.5")
        self.assertEqual(num_token.number, 2.5)
        self.assertEqual(num_token.original, "zwei einhalb")
        self.assertEqual(num_token.spanned_original, (num_token.original, original_span))  # ("zwei einhalb", (20, 32))

        # unconverted ordinal
        tokens = self.parser.convert_words_to_numbers("das ist der dritte test")
        sp1, sp2, _ = word_tokenize("das ist der dritte test", spans=True)[3]
        original_span = (sp1, sp2)
        self.assertEqual(tokens.text, "das ist der dritte test")
        self.assertEqual(tokens.word_list, ["das", "ist", "der", "dritte", "test"])
        num_token = tokens[3]
        self.assertFalse(num_token.isNumeric)
        self.assertFalse(num_token.isDigit)
        self.assertTrue(num_token.isOrdinal)
        self.assertEqual(num_token.word, "dritte")
        self.assertEqual(num_token.number, 3)
        self.assertEqual(num_token.original, "dritte")
        self.assertEqual(num_token.spanned_original, (num_token.original, (12, 18)))

        # converted ordinal
        tokens = self.parser.convert_words_to_numbers("das ist der dritte test", ordinals=True)
        sp1, sp2, _ = word_tokenize("das ist der dritte test", spans=True)[3]
        original_span = (sp1, sp2)
        self.assertEqual(tokens.text, "das ist der 3. test")
        self.assertEqual(tokens.word_list, ["das", "ist", "der", "3.", "test"])
        num_token = tokens[3]
        self.assertFalse(num_token.isNumeric)
        self.assertFalse(num_token.isDigit)
        self.assertTrue(num_token.isOrdinal)
        self.assertEqual(num_token.word, "3.")
        self.assertEqual(num_token.number, 3)
        self.assertEqual(num_token.original, "dritte")
        self.assertEqual(num_token.spanned_original, (num_token.original, original_span))  # ("dritte", (12, 18)))

        # correctly tagged ordinal numbers
        tokens = self.parser.convert_words_to_numbers("das ist der 3. test", ordinals=True)
        self.assertEqual(tokens.text, "das ist der 3. test")
        self.assertEqual(tokens.word_list, ["das", "ist", "der", "3.", "test"])
        self.assertFalse(num_token.isNumeric)
        self.assertFalse(num_token.isDigit)
        self.assertTrue(num_token.isOrdinal)
        self.assertEqual(num_token.number, 3)
        
        self.assertEqual(self.parser.convert_words_to_numbers("das ist der 4/5 test").text,
                         f"das ist der {4/5} test")
        
        # number -> time conversion
        self.assertEqual(self.parser.convert_words_to_numbers("es ist 4.30 Uhr").text,
                         f"es ist 4:30 Uhr")
        self.assertEqual(self.parser.convert_words_to_numbers("es ist halb acht").text,
                         f"es ist 7:30")

    def test_numbers(self):

        def test_xtract(utt, expected_numbers,
                             ordinals=False,
                             fractions=True,
                             short_scale=True):
            # extract_numbers
            numbers = [n.value for n in self.parser.extract_numbers(utt,
                                                                    ordinals=ordinals,
                                                                    fractions=fractions,
                                                                    short_scale=short_scale)]            
            if not isinstance(expected_numbers, list):
                expected_numbers = [expected_numbers]
            self.assertEqual(numbers, expected_numbers)

        test_xtract("das ist test nummer zwei", 2)
        test_xtract("das ist test nummer zwei einhalb", 2.5)
        test_xtract("das ist der dritte test", [])
        test_xtract("das ist der dritte test", 3, ordinals=True)
        test_xtract("das ist test nummer eins 2 drei", [1, 2, 3])

        test_xtract("das ist ein eins zwei drei  test", [1, 2, 3])
        test_xtract("das ist ein vier fünf sechs  test", [4, 5, 6])
        test_xtract("das ist ein sieben acht neun  test", [7, 8, 9])
        test_xtract("das ist ein zehn elf zwölf  test", [10, 11, 12])
        test_xtract("test einundzwanzig", 21)
        test_xtract("ein und zwanzig", 21)
        test_xtract("eins und zwei", [1, 2])
        test_xtract("1 Hund, sieben Schweine, Macdonald hatte eine Farm, 3 mal 5 Macarena", [1, 7, 1, 3, 5])
        test_xtract("zwei biere für zwei bären", [2, 2])
        test_xtract("zwanzig 20 zwanzig", [20, 20, 20])
        test_xtract("zwanzig 20 22", [20, 20, 22])
        test_xtract("zwanzig zwanzig zwei und zwanzig", [20, 20, 22])
        test_xtract("dritte", [])
        test_xtract("dritte", 3, ordinals=True)
        test_xtract("ein drittel", 1/3)
        test_xtract("eindrittel", 1/3)
        test_xtract("ein eindrittel", 1 + (1/3))
        test_xtract("in einer halben stunde", 0.5)
        test_xtract("wir haben tausende tests zur auswahl", 1000)
        test_xtract("sechs trillionen", 6e18)
        test_xtract("zwei Schweine und sechs Billionen Bakterien", [2, 6000000000000])
        test_xtract("einunddreißigsten oder ersten", [31, 1], ordinals=True)
        test_xtract("Das ist ein sieben acht neuneinhalb Test", [7.0, 8.0, 9.5])

        test_xtract("grobo 0", 0)
        test_xtract("ein paar biere", 1)
        test_xtract("ein paar hundert biere", [1, 100])
        test_xtract("total 100%", 100)

        test_xtract("1/3 Tassen", 1.0 / 3.0)
        test_xtract("viertel Tasse", 1.0 / 4.0)
        test_xtract("eine viertel tasse", 0.25)
        test_xtract("1/4 Tasse", 0.25)
        test_xtract("2/3 Tasse", 2.0 / 3.0)
        test_xtract("3/4 Tasse", 3.0 / 4.0)
        test_xtract("1 und 3/4 tassen", 1.75)
        test_xtract("1 und eine halbe Tasse", 1.5)
        test_xtract("hälfte einer tomate", 0.5)
        test_xtract("eine Tasse und eine halbe (tomate)", [1, 0.5])
        test_xtract("zwei und zwei hälften", 3)
        test_xtract("auf halbem weg", 0.5)
        test_xtract("drei viertel Tassen", [], fractions=False)
        test_xtract("drei viertel Tassen", 3.0 / 4.0)
        test_xtract("zweiundzwanzig", 22)
        test_xtract("zwei und zwanzig", 22)
        test_xtract("dreihundertvierundneunzig", 394)
        test_xtract("dreihundertvier und neunzig", 394)
        test_xtract("drei hundert vierundneunzig", 394)
        test_xtract("zwei hundertste", 200, ordinals=True)
        test_xtract("zweihundertste", 200, ordinals=True)
        test_xtract("zwei hundertste", [])
        test_xtract("zwei hundertstel", 2/100)
        test_xtract("neun tausend", 9000)
        test_xtract("sechs hundert sechs und sechzig", 666)
        test_xtract("zwei millionen", 2000000)
        test_xtract("zwei millionen fünf hundert tausend tonnen", 2500000)
        test_xtract("2,6 millionen tonnen", 2600000)
        test_xtract("2 komma 6 millionen tonnen", 2600000)
        test_xtract("sechs trillionen", 6000000000000000000)
        test_xtract("eins komma fünf vier", 1.54)
        test_xtract("komma fünf", 0.5)
        test_xtract("null komma fünf", 0.5)
        test_xtract("billionen jahre älter", 1000000000000)
        test_xtract("ein hundert tausend", 100000)
        test_xtract("minus 2", -2)
        test_xtract("3 tausend millionen", 3000000000)

        # suppress fractional and ordinal
        test_xtract("zum hundertsten mal, ich sagte zwei nicht zwei drittel", 2, fractions=False)

        # sanity check
        test_xtract("dritte", 3, ordinals=True)
        test_xtract("sechste", 6, ordinals=True)

        # test explicit ordinals
        test_xtract("am 1. November", 1, ordinals=True)
        test_xtract("am 31. Dezember", 31, ordinals=True)
        test_xtract("am 1. November", [])
        
        # test non ambiguous ordinals
        test_xtract("das ist der erste test", 1, ordinals=True)

        # test ambiguous time unit
        test_xtract("halb acht", [], fractions=False)
        test_xtract("halb acht", [])
        # only done with consecutive numbers, 
        # dont want to bring in nother markers for this -> time parser
        test_xtract("viertel nach acht", [0.25, 8])
        ## this time unit gets parsed as float -> corrected in conversion; no number
        test_xtract("9.33 Uhr am zwanzigsten Mai 2020", [20, 2020], ordinals=True)


    def test_number(self):

        def _extract_number(utt, expected_number,
                             ordinals=False,
                             fractions=True,
                             short_scale=True):
            
            number = self.parser.extract_number(utt,
                                                ordinals=ordinals,
                                                fractions=fractions,
                                                short_scale=short_scale)
            
            val = number.value if number else None
            self.assertEqual(val, expected_number)

        # NOTE directly following (unrelated) whole numbers "twenty 22" will return the last number first
        # this is hard to tackle with the present code 

        _extract_number("das ist test eins von zwei", 1)
        _extract_number("das ist test zwei einhalb von 3", 2.5)
        _extract_number("das ist der erste test von 2", 2)
        _extract_number("das ist der erste test von 2", 1, ordinals=True)
        
        _extract_number("1 Hund, sieben Schweine, Macdonald hatte eine Farm, 3 mal 5 Macarena", 1)
        _extract_number("zweiundzwanzig mal 2", 22)
        _extract_number("der dritte ist sechzig", 60)
        _extract_number("der dritte ist sechzig", 3, ordinals=True)
        _extract_number("auf halbem weg zu 60", 60, fractions=False)
        _extract_number("zwei Schweine und sechs Billionen Bakterien", 2)
        _extract_number("einundfünfzigste Woche in einem Jahr", 1)
        _extract_number("einundfünfzigste Woche in einem Jahr", 51, ordinals=True)
        _extract_number("zum hundertsten mal, ich sagte zwei nicht zwei drittel", 2)
        _extract_number("zum hundertsten mal, ich sagte zwei nicht zwei drittel", 100, ordinals=True)
        _extract_number("zum hundertsten mal, ich sagte zwei drittel nicht zwei", 2/3)
        _extract_number("zum hundertsten mal, ich sagte zwei drittel nicht zwei", 2, fractions=False)
        _extract_number("1. ein tequilla", 1)
        _extract_number("2. ein halber löffel salz", 0.5)
        _extract_number("3. zitrone", None)
        _extract_number("50% von 100", 50)
        _extract_number("minus 50 grad in zwei städten", -50)
        _extract_number("komma sechs von sechs", 0.6)
        _extract_number("zwei millionen fünf hundert tausend sechs hundert sechs und sechzig komma sechs tonnen", 2500666.6)


if __name__ == "__main__":
    unittest.main()