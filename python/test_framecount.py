"""Checks on the frame-to-raw-text mapping.

The passage in `test_passage_counted_by_hand` was written to contain every
countable frame at least once, counted by hand before this file ran, and the
expected counts below are those hand counts. It is the check SCOPE.md asks for:
the mapping has to reproduce the interface's matching rather than be assumed to.

Run from the repository root: python -m pytest python -q
"""

from pathlib import Path

import pytest

from framecount import (count_frames, count_pattern, load_frames, parse_query,
                        tokenise, word_count)

REPO = Path(__file__).resolve().parent.parent

# Sentence by sentence, with the frame each one carries:
#   1  here 's the thing      (curly apostrophe, sentence-initial capital)
#   2  it 's not * , it 's
#   3  it 's not just
#   4  here 's what
#   5  the thing is / and that 's / is n't just
#   6  turns out / the real question is
#   7  not * , but *
#   8  not just * but
#   9  that 's the whole point
#  10  which is the point
PASSAGE = (
    "Here’s the thing: the model doesn't stop there. "
    "It's not fluent, it's American. "
    "It's not just a house style either. "
    "Here's what the counts show. "
    "The thing is, and that's the part that matters, it isn't just a habit. "
    "Turns out the real question is which reader you have in mind. "
    "Not grammar, but rhythm. "
    "Not just American but ordinary. "
    "That's the whole point. "
    "Which is the point."
)

HAND_COUNTS = {
    "F01": 1, "F02": 0, "F03": 1, "F04": 1, "F05": 0, "F06": 1, "F07": 1,
    "F08": 1, "F09": 1, "F10": 1, "F11": 1, "F12": 1, "F13": 1, "F14": 1,
    "F15": 1,
}


@pytest.fixture(scope="module")
def frames():
    return load_frames(REPO / "data" / "frames.csv")


def test_clitics_split_off():
    assert tokenise("Here's the thing") == ["here", "'s", "the", "thing"]
    assert tokenise("isn't just") == ["is", "n't", "just"]
    assert tokenise("we'll, we've, we're, I'd, I'm") == [
        "we", "'ll", ",", "we", "'ve", ",", "we", "'re", ",", "i", "'d", ",",
        "i", "'m"]


def test_curly_punctuation_folds_to_ascii():
    assert tokenise("Here’s the thing") == tokenise("Here's the thing")
    assert tokenise("“quoted”") == ['"', "quoted", '"']


def test_hyphenated_word_is_one_token():
    # GloWbE's List display for `here 's the * part` returns forms such as
    # "here 's the sad-but-true part", so a hyphenated compound fills the
    # single-token slot.
    assert tokenise("the sad-but-true part") == ["the", "sad-but-true", "part"]
    tokens = tokenise("Here's the mind-bending part.")
    assert count_pattern(tokens, parse_query("here 's the * part")) == 1


def test_dashes_stay_their_own_token():
    assert tokenise("a—b") == ["a", "-", "b"]
    assert tokenise("a - b") == ["a", "-", "b"]


def test_punctuation_is_its_own_token():
    assert tokenise("it's not just, it's") == [
        "it", "'s", "not", "just", ",", "it", "'s"]


def test_lone_apostrophe_separates():
    assert tokenise("the writers' room") == ["the", "writers", "'", "room"]


def test_word_count_excludes_punctuation():
    assert word_count(tokenise("Here's the thing.")) == 4


def test_wildcard_matches_exactly_one_token():
    tokens = tokenise("here's the best part and here's the very best part")
    assert count_pattern(tokens, parse_query("here 's the * part")) == 1


def test_matches_may_overlap():
    tokens = tokenise("and that's and that's")
    assert count_pattern(tokens, parse_query("and that 's")) == 2


def test_empty_pattern_is_refused():
    with pytest.raises(ValueError):
        count_pattern(["a"], [])


def test_passage_counted_by_hand(frames):
    counts = count_frames(PASSAGE, frames)
    got = {frame_id: counts[frame_id] for frame_id in HAND_COUNTS}
    assert got == HAND_COUNTS


def test_every_frozen_frame_is_countable_here(frames):
    # F06 cannot be counted in GloWbE on a free account (deviation D2), but it
    # is countable in raw text, and Studies 2 and 3 report it.
    assert len(frames) == 15
    assert all(pattern for pattern in frames.values())
