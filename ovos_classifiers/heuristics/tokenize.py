import re
from dataclasses import dataclass
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta, time
from typing import List, Union, Optional, Iterator, Callable, Any, Tuple, overload

from ovos_utils import flatten_list
from quebra_frases import word_tokenize as _wtok, sentence_tokenize as _stok
from quebra_frases import span_indexed_word_tokenize

# Token is intended to be used in the number processing functions in
# this module.
@dataclass
class Token:
    word : str
    index: int
    span: tuple = ()
    _original: Optional[str] = None

    # analytic flags
    isConsumed: bool = False
    isOrdinal: Union[bool, int] = False
    _ordinalIdx: Optional[int] = None
    isDate: bool = False
    isTime: bool = False
    isDuration: bool = False

    @property
    def original(self) -> Optional[str]:
        return self._original or self.word
    
    @original.setter
    def original(self, value: str):
        self._original = value

    @property
    def isDigit(self) -> bool:
        return self.word.isdigit()
    
    @property
    def isNumeric(self) -> bool:
        return True if re.search(r'(?<!\S)-?\d+([\.\,]\d+)?(?!\S)', self.word) else False
    
    @property
    def isSymbolic(self) -> bool:
        return self.word in [",", ".", ";", "_", "!", "?", "<", ">",
                             "|", "(", ")", "=", "[", "]", "{",
                             "}", "»", "«", "*", "~", "^", "`"]  # "-"
    
    @property
    def isComma(self) -> bool:
        return self.word == ","
    
    @property
    def number(self) -> Union[int, float, None]:
        if self.isOrdinal:
            return self._ordinalIdx
        elif self.isNumeric:
            _fac = -1 if self.word.startswith("-") else 1
            _num = self.word.replace(",", ".").lstrip("-")
            _num = float(_num) if '.' in self.word else int(_num)
            return _num * _fac
        else:
            return None
    
    @property
    def lowercase(self) -> str:
        return self.word.lower()
    
    @property
    # TODO: Quebra frases: Maybe change span tuple into (str, (x, y))
    # TODO Let this set by replace function
    # no reference to self.span as this might be changed multiple times
    # _orginal = (original, (start, end))
    # return self._original
    # def orgiginal: return self._original[0]
    def spanned_original(self) -> tuple:
        if self.original is None:
            return (self.word, self.span)
        return (self.original, (self.span[0],
                                self.span[0] + len(self.original)))


class Tokens():
    def __init__(self,
                 input: Union[str, List[str], List[Token], 'Tokens'],
                 lang: Optional[str] = None):
        self._tokens: List[Token] = []
        self.lang = lang or "en-us"
        if isinstance(input, str):
            self.tokenize(input)
        # list of strings, unknown if tokenized
        elif isinstance(input, list) and len(input) and \
                isinstance(input[0], str):
            self.tokenize(" ".join(input))
        # Tokens / list of Token
        else:
            self._tokens = [tok for tok in input]
    
    def __len__(self):
        return len(self._tokens)
    
    def __bool__(self):
        return bool(len(self._tokens))
    
    def __iter__(self) -> Iterator[Token]:
        return iter(self._tokens)
    
    @overload
    def __getitem__(self, index: int) -> Token:
        ...

    @overload
    def __getitem__(self, index: Union[slice, Tuple[int, int]]) -> 'Tokens':
        ...

    def __getitem__(self, index: Union[int, slice, Tuple[int, int]]):
        if isinstance(index, tuple):
            return self.__getitem_span(index)
        elif isinstance(index, int):
            for t in self._tokens:
                if t.index == index:
                    return t  # Token
            return Token("", -1)  # empty token
        elif isinstance(index, slice):
            return Tokens([tok for tok in self._tokens
                           if (index.start is None or index.start <= tok.index)
                           and (index.stop is None or tok.index < index.stop)])
        # raise IndexError("Index out of range")
    
    def __getitem_span(self, index: Tuple[int, int]) -> Optional['Tokens']:
        if len(index) != 2:
            raise ValueError("Span index must be a tuple of length 2")
        
        start = index[0]
        end = index[1]
        start_found = False
        end_found = False
        _tokens = []

        for token in self.tokens:
            if not start_found and token.span[0] == start:
                start_found = True
            if start_found:
                _tokens.append(token)
            if token.span[1] == end:
                end_found = True
                break
        
        if not start_found and not end_found:
            _tokens = []
        return Tokens(_tokens)

    def __setitem__(self, index, value):
        if not isinstance(value, Token):
            raise ValueError("Tokens can only be set with Token objects")
        self._tokens[index] = value
        self.__reindex()
    
    @property
    def start_index(self) -> int:
        return self._tokens[0].index

    @property
    def end_index(self) -> int:
        return self._tokens[-1].index
    
    @property
    def word_list(self) -> List[str]:
        return [t.word for t in self._tokens]
    
    @property
    def tokens(self) -> List[Token]:
        return self._tokens
    
    # join them appropriately
    @property
    def text(self) -> str:
        """
        Reconstruct the string according to token.span attribute.
        """
        _text = ""
        for token in self._tokens:
            _start = token.span[0]
            if _start > len(_text):
                _text += " " * (_start - len(_text))
            elif _start < len(_text):
                _text += " "
            _text += token.word
        return _text
    
    @property
    def lowercase(self) -> str:
        return self.text.lower()
    
    @property
    def remaining_text(self) -> str:
        return self._join_tokens([t.original or t.word for t in self._tokens
                                  if not t.isConsumed])
    
    @property
    def remaining(self) -> List[Token]:
        return [t for t in self._tokens if not t.isConsumed]
    
    # get word with a specific index
    def word(self, index: int) -> str:
        return self._tokens[index].word if \
                self.start_index <= index <= self.end_index else ""
    
    # get token with a specific index
    def token(self, index: int) -> Optional[Token]:
        return self._tokens[index] if \
                self.start_index <= index <= self.end_index else None
        
    def tokenize(self, input: str):
        self._tokens = [Token(siwt[2], i, siwt[:2])
                        for i, siwt in enumerate(word_tokenize(input,
                                                               self.lang,
                                                               spans=True))]
    
    def _join_tokens(self, tokens: Optional[List[str]] = None):
        if tokens is None:
            return re.sub(' +', ' ', self.text)
        concatenated_tokens = []
        prev_token = None
        for token in tokens:
            if prev_token is not None and token in ".,;?!>)]}»`":
                concatenated_tokens[-1] += token
            elif prev_token is not None and prev_token in "<([{«*~^`":
                concatenated_tokens[-1] += token
            else:
                concatenated_tokens.append(token)
            prev_token = token
        return " ".join(concatenated_tokens)
    
    def __reindex(self):
        """
        Reindex tokens and recalculate spans.
        """
        spans = word_tokenize(self._join_tokens(),
                              self.lang, spans=True)
        _start_span = self._tokens[0].span[0]
        for idx, token in enumerate(self._tokens):
            token.index = idx + self._tokens[0].index
            _start, _end = spans[idx][:2]
            token.span = (_start + _start_span,
                          _end + _start_span)

    # replace a list of tokens with the replacement string
    def replace(self, replacement: str, tokens: List[Token]):
        """
        Replace tokens with a new string.        
        """
        # TODO raise if not consecutive
        tokens.sort(key=lambda t: t.index)
        start_idx = tokens[0].index
        end_idx = tokens[-1].index
        start_span = tokens[0].span[0]

        orig = []
        delete = []
        repl_index = -1
        for idx, tok in enumerate(self._tokens):
            if start_idx <= tok.index <= end_idx:
                orig.append(tok.word)
                if start_idx == tok.index:
                    repl_index = idx
                    continue
                delete.append(idx)

        if delete:
            del self._tokens[min(delete):max(delete)+1]
        repl_token = self._tokens[repl_index]
        repl_token.word = replacement
        repl_token.span = (start_span, start_span + len(replacement))
        repl_token.original = " ".join(orig)

        self.__reindex()
    
    def find(self, match: Union[List[str], Callable],
                   allow_consumed: bool = True,
                   reverse: bool = False) -> Optional[Token]:
        """
        This function iterates through the list of words, and checks each word against
        the list of tokens. If the word is in the list of tokens, the token is returned.
        """
        _tokens = reversed(self.tokens) if reverse else self.tokens
        if isinstance(match, Callable):
            for token in _tokens:
                if not allow_consumed and token.isConsumed:
                    continue
                if match(token):
                    return token
        elif isinstance(match, list):
            for token in _tokens:
                if not allow_consumed and token.isConsumed:
                    continue
                for word in match:
                    if token.word == word.capitalize() or \
                            token.word == word.lower():
                        return token
        return None
    
    def find_tag(self, tag: str,
                       value: Any = True, 
                       allow_consumed: bool = True,
                       reverse: bool = False) -> Optional[Token]:
        """
        This function iterates through the list of words, and checks each word against
        the list of tokens. If the word is in the list of tokens, the token is returned.
        """
        _tokens = reversed(self.tokens) if reverse else self.tokens
        for token in _tokens:
            if not allow_consumed and token.isConsumed:
                continue
            if hasattr(token, tag) and getattr(token, tag) == value:
                return token
        return None
    
    def partition(self, split_on: Callable) -> List['Tokens']:
        """
        Split the Tokens into multiple Tokens objects, based on the split_on function.
        """
        partitions = []
        partition = []
        for token in self._tokens:
            if split_on(token):
                partitions.append(Tokens(partition))
                partitions.append(Tokens([token]))
                partition = []
            else:
                partition.append(token)
        if partition:
            partitions.append(Tokens(partition))
        return partitions
    
    def consume(self, token: Union[Token, List[Token], None]):
        if token is None:
            return
        if isinstance(token, Token):
            token = [token]
        for tok in token:
            for t in self._tokens:
                if t.span == tok.span:
                    t.isConsumed = True
    
    def reset_consumed(self, exceptions: Optional[List[Token]] = None):
        for token in self._tokens:
            if exceptions and token in exceptions:
                continue
            token.isConsumed = False

    def __repr__(self):
        return f"Tokens({[repr(token) for token in self._tokens]})"
    
    def __str__(self):
        return self.text


class ReplaceableEntity(Tokens):
    """
    Similar to Token, this class is used in entity parsing.

    Once we've found an entity in a string, this class contains all
    the info about the value, and where it came from in the original text.
    In other words, it is the text, and the entity that can replace it in
    the string.
    """

    def __init__(self, value: Any, tokens: List):
        self.value = value
        # might be empty list
        if tokens:
            super().__init__(tokens)

    @property
    def type(self):
        return type(self.value)

    def __bool__(self):
        return bool(self.value is not None and self.value is not False)

    def __str__(self):
        return "({v}, {t})".format(v=self.value, t=self._tokens)

    def __repr__(self):
        return "{n}({v}, {t})".format(n=self.__class__.__name__, v=self.value,
                                      t=[t.original or t.word for t in self._tokens])


class ReplaceableNumber(ReplaceableEntity):
    """
    Similar to Token, this class is used in number parsing.

    Once we've found a number in a string, this class contains all
    the info about the value, and where it came from in the original text.
    In other words, it is the text, and the number that can replace it in
    the string.
    """


class ReplaceableDate(ReplaceableEntity):
    """
    Similar to Token, this class is used in date parsing.

    Once we've found a date in a string, this class contains all
    the info about the value, and where it came from in the original text.
    In other words, it is the text, and the date that can replace it in
    the string.
    """

    def __init__(self, value: date, tokens: List):
        if isinstance(value, datetime):
            value = value.date()
        assert isinstance(value, date)
        super().__init__(value, tokens)


class ReplaceableTime(ReplaceableEntity):
    """
    Similar to Token, this class is used in date parsing.

    Once we've found a time in a string, this class contains all
    the info about the value, and where it came from in the original text.
    In other words, it is the text, and the time that can replace it in
    the string.
    """

    def __init__(self, value: time, tokens: List):
        if isinstance(value, datetime):
            value = value.time()
        assert isinstance(value, time)
        super().__init__(value, tokens)


class ReplaceableDatetime(ReplaceableEntity):
    """
    Similar to Token, this class is used in date parsing.

    Once we've found a time in a string, this class contains all
    the info about the value, and where it came from in the original text.
    In other words, it is the text, and the time that can replace it in
    the string.
    """

    def __init__(self, value: datetime, tokens: List):
        assert isinstance(value, datetime)
        super().__init__(value, tokens)


class ReplaceableTimedelta(ReplaceableEntity):
    """
    Similar to Token, this class is used in date parsing.

    Once we've found a timedelta in a string, this class contains all
    the info about the value, and where it came from in the original text.
    In other words, it is the text, and the duration that can replace it in
    the string.
    """

    def __init__(self,
                 value: Union[timedelta, relativedelta],
                 tokens: List):
        assert isinstance(value, timedelta) or isinstance(value, relativedelta)
        super().__init__(value, tokens)


def partition_list(items, split_on):
    """
    Partition a list of items.

    Works similarly to str.partition

    Args:
        items:
        split_on callable:
            Should return a boolean. Each item will be passed to
            this callable in succession, and partitions will be
            created any time it returns True.

    Returns:
        [[any]]

    """
    splits = []
    current_split = []
    for item in items:
        if split_on(item):
            splits.append(current_split)
            splits.append([item])
            current_split = []
        else:
            current_split.append(item)
    splits.append(current_split)
    return list(filter(lambda x: len(x) != 0, splits))


def sentence_tokenize(text):
    sents = [_stok(s) for s in text.split("\n")]
    return flatten_list(sents)


# Lets prepare specific languages for tokenization,
# not bypass the tokenizer completely and simply split
# This makes the achievements in the QF tokenizer irrelevant
# If a language needs special regexes, it should be added here
def word_tokenize(utterance: str,
                  lang: Optional[str] = None,
                  spans: bool = False):
    if lang is not None and lang.startswith("pt"):
        return word_tokenize_pt(utterance)
    elif lang is not None and lang.startswith("ca"):
        return word_tokenize_ca(utterance)
    elif lang is not None and lang.startswith("de"):
        # split on hyphens 
        utterance = re.sub(r"\b([A-Z][a-z]*|[0-9]*)-([A-Za-z][a-z]*)\b", r"\1 \2", utterance)
    # Split things like 12%
    utterance = re.sub(r"([0-9]+)([\%])", r"\1 \2", utterance)
    # Split thins like #1
    utterance = re.sub(r"(\#)([0-9]+\b)", r"\1 \2", utterance)
    if spans:
        return span_indexed_word_tokenize(utterance)
    return _wtok(utterance)


def word_tokenize_pt(utterance):
    # Split things like 12%
    utterance = re.sub(r"([0-9]+)([\%])", r"\1 \2", utterance)
    # Split things like #1
    utterance = re.sub(r"(\#)([0-9]+\b)", r"\1 \2", utterance)
    # Split things like amo-te
    utterance = re.sub(r"([a-zA-Z]+)(-)([a-zA-Z]+\b)", r"\1 \2 \3",
                       utterance)
    tokens = utterance.split()
    if tokens[-1] == '-':
        tokens = tokens[:-1]

    return tokens


def word_tokenize_ca(utterance):
    # Split things like 12%
    utterance = re.sub(r"([0-9]+)([\%])", r"\1 \2", utterance)
    # Split things like #1
    utterance = re.sub(r"(\#)([0-9]+\b)", r"\1 \2", utterance)
    # Don't split at -
    tokens = utterance.split()
    if tokens[-1] == '-':
        tokens = tokens[:-1]

    return tokens


def subword_tokenize(utterance):
    """phonetically meaningful subwords,
    Pronunciation-assisted Subword Modeling, generates linguistically
    meaningful subwords by analyzing a corpus and a dictionary.

    @inproceedings{xu2019improving,
        title={Improving End-to-end Speech Recognition with Pronunciation-assisted Sub-word Modeling},
        author={Xu, Hainan and Ding, Shuoyang and Watanabe, Shinji},
        booktitle={ICASSP 2019-2019 IEEE International Conference on Acoustics, Speech and Signal Processing (ICASSP)},
        pages={7110--7114},
        year={2019},
        organization={IEEE}
    }

    see https://github.com/hainan-xv/PASM
    """
    from ovos_classifiers.heuristics.phonemizer import EnglishARPAHeuristicPhonemizer
    return EnglishARPAHeuristicPhonemizer.subword_tokenize(utterance)


def syllable_tokenize(utterance):
    """
    The Sonority Sequencing Principle (SSP) is a language agnostic algorithm proposed
    by Otto Jesperson in 1904. The sonorous quality of a phoneme is judged by the
    openness of the lips. Syllable breaks occur before troughs in sonority. For more
    on the SSP see Selkirk (1984).

    The default implementation uses the English alphabet, but the `sonority_hiearchy`
    can be modified to IPA or any other alphabet for the use-case. The SSP is a
    universal syllabification algorithm, but that does not mean it performs equally
    across languages. Bartlett et al. (2009) is a good benchmark for English accuracy
    if utilizing IPA (pg. 311).

    Importantly, if a custom hierarchy is supplied and vowels span across more than
    one level, they should be given separately to the `vowels` class attribute.

    References:

    - Otto Jespersen. 1904. Lehrbuch der Phonetik.
      Leipzig, Teubner. Chapter 13, Silbe, pp. 185-203.
    - Elisabeth Selkirk. 1984. On the major class features and syllable theory.
      In Aronoff & Oehrle (eds.) Language Sound Structure: Studies in Phonology.
      Cambridge, MIT Press. pp. 107-136.
    - Susan Bartlett, et al. 2009. On the Syllabification of Phonemes.
      In HLT-NAACL. pp. 308-316.
    """
    from nltk.tokenize.sonority_sequencing import SyllableTokenizer
    return SyllableTokenizer().tokenize(utterance)
