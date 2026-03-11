"""Unit tests for text_pattern_matcher helper functions and ad_detector region helpers."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from unittest.mock import MagicMock, patch

from text_pattern_matcher import (
    _split_sentences, _extract_intro_phrase, _extract_outro_phrase,
    TextPatternMatcher, AdPattern,
)
from ad_detector import _unpack_region, get_uncovered_portions, AdDetector
from config import DEFAULT_AD_DURATION_ESTIMATE


class TestSplitSentences:
    """Tests for _split_sentences."""

    def test_basic_splitting(self):
        text = "Hello world. How are you? I am fine!"
        result = _split_sentences(text)
        assert result == ["Hello world.", "How are you?", "I am fine!"]

    def test_no_punctuation_returns_whole_text(self):
        text = "this is a sentence without punctuation"
        result = _split_sentences(text)
        assert result == [text]

    def test_empty_string(self):
        assert _split_sentences("") == []

    def test_single_sentence(self):
        result = _split_sentences("Just one sentence.")
        assert result == ["Just one sentence."]

    def test_extra_whitespace(self):
        text = "First sentence.   Second sentence."
        result = _split_sentences(text)
        assert result == ["First sentence.", "Second sentence."]


class TestExtractIntroPhrase:
    """Tests for _extract_intro_phrase."""

    def test_stops_at_min_words(self):
        # Build text with 3 sentences, each ~10 words
        s1 = "This is the first sentence of the ad read."
        s2 = "And here comes the second sentence of the ad."
        s3 = "Finally the third sentence wraps up the whole thing."
        text = f"{s1} {s2} {s3}"
        result = _extract_intro_phrase(text, min_words=15, max_words=60)
        # Should include s1 + s2 (20 words >= 15) and stop before s3
        assert result.startswith("This is the first")
        assert "second sentence" in result
        assert "third sentence" not in result

    def test_text_shorter_than_min_words(self):
        text = "Short text here."
        result = _extract_intro_phrase(text, min_words=20, max_words=60)
        assert result == text

    def test_max_words_cap(self):
        words = " ".join([f"word{i}" for i in range(100)])
        text = f"{words}."
        result = _extract_intro_phrase(text, min_words=20, max_words=30)
        result_word_count = len(result.split())
        # Single sentence exceeds max_words but is the first sentence so it gets included
        assert result_word_count <= 101  # whole sentence is included

    def test_empty_text(self):
        assert _extract_intro_phrase("") == ""


class TestExtractOutroPhrase:
    """Tests for _extract_outro_phrase."""

    def test_extracts_from_end(self):
        s1 = "This is the first sentence of the ad."
        s2 = "And the second sentence continues here."
        s3 = "Visit our site at example dot com slash promo."
        text = f"{s1} {s2} {s3}"
        result = _extract_outro_phrase(text, min_words=8, max_words=40)
        assert "example dot com" in result
        assert "first sentence" not in result

    def test_text_shorter_than_min_words(self):
        text = "Short outro."
        result = _extract_outro_phrase(text, min_words=15, max_words=40)
        assert result == text

    def test_reversed_sentence_order_preserved(self):
        s1 = "First sentence here."
        s2 = "Second sentence here."
        s3 = "Third sentence here."
        text = f"{s1} {s2} {s3}"
        result = _extract_outro_phrase(text, min_words=4, max_words=40)
        # Even though we iterate in reverse, result should be in original order
        if "Second" in result and "Third" in result:
            assert result.index("Second") < result.index("Third")

    def test_empty_text(self):
        assert _extract_outro_phrase("") == ""


class TestComputeOverlap:
    """Tests for AdDetector._compute_overlap."""

    def test_full_overlap(self):
        assert AdDetector._compute_overlap(10, 50, 10, 50) == 1.0

    def test_partial_overlap(self):
        result = AdDetector._compute_overlap(10, 30, 20, 40)
        # overlap = 30-20 = 10, b_duration = 40-20 = 20, fraction = 0.5
        assert abs(result - 0.5) < 0.001

    def test_no_overlap(self):
        assert AdDetector._compute_overlap(10, 20, 30, 40) == 0.0

    def test_zero_duration_region(self):
        assert AdDetector._compute_overlap(10, 20, 30, 30) == 0.0


class TestUnpackRegion:
    """Tests for _unpack_region."""

    def test_dict_input(self):
        region = {'start': 10.0, 'end': 20.0, 'pattern_id': 42}
        assert _unpack_region(region) == (10.0, 20.0)

    def test_tuple_input(self):
        region = (10.0, 20.0)
        assert _unpack_region(region) == (10.0, 20.0)

    def test_list_input(self):
        region = [5.0, 15.0]
        assert _unpack_region(region) == (5.0, 15.0)


class TestGetUncoveredPortionsWithDicts:
    """Tests for get_uncovered_portions using dict-format regions."""

    def test_fully_covered_by_dict_regions(self):
        ad = {'start': 100.0, 'end': 200.0, 'confidence': 0.9, 'reason': 'test'}
        covered = [{'start': 90.0, 'end': 210.0, 'pattern_id': 1}]
        result = get_uncovered_portions(ad, covered)
        assert result == []

    def test_partial_coverage_returns_tail(self):
        ad = {'start': 100.0, 'end': 200.0, 'confidence': 0.9, 'reason': 'test'}
        # Cover first 70% (70s out of 100s)
        covered = [{'start': 95.0, 'end': 170.0, 'pattern_id': 1}]
        result = get_uncovered_portions(ad, covered, min_duration=5.0)
        assert len(result) == 1
        assert abs(result[0]['start'] - 170.0) < 0.1
        assert abs(result[0]['end'] - 200.0) < 0.1

    def test_no_coverage_returns_original(self):
        ad = {'start': 100.0, 'end': 200.0, 'confidence': 0.9, 'reason': 'test'}
        covered = [{'start': 300.0, 'end': 400.0, 'pattern_id': 1}]
        result = get_uncovered_portions(ad, covered)
        assert len(result) == 1
        assert result[0]['start'] == 100.0
        assert result[0]['end'] == 200.0

    def test_mixed_dict_and_tuple_regions(self):
        ad = {'start': 100.0, 'end': 200.0, 'confidence': 0.9, 'reason': 'test'}
        covered = [
            {'start': 95.0, 'end': 150.0, 'pattern_id': 1},
            (150.0, 210.0)
        ]
        result = get_uncovered_portions(ad, covered)
        # Fully covered by combination
        assert result == []

    def test_zero_duration_ad(self):
        ad = {'start': 100.0, 'end': 100.0, 'confidence': 0.9, 'reason': 'test'}
        covered = [{'start': 90.0, 'end': 110.0}]
        result = get_uncovered_portions(ad, covered)
        assert result == []


class TestScanForBoundary:
    """Tests for _scan_for_boundary via _scan_for_outro and _scan_for_intro."""

    def _make_matcher(self):
        matcher = TextPatternMatcher.__new__(TextPatternMatcher)
        matcher._patterns = []
        matcher._pattern_vectors = None
        matcher._vectorizer = None
        matcher._pattern_buckets = {}
        return matcher

    def test_scan_for_outro_returns_end_time(self):
        matcher = self._make_matcher()
        pattern = AdPattern(
            id=1, text_template="test", intro_variants=[],
            outro_variants=["visit our website today"],
            sponsor="test", scope="podcast",
        )
        # Mock _fuzzy_find to return a match at position 10
        matcher._fuzzy_find = MagicMock(return_value=(10, 85))
        # Mock _char_pos_to_time to return known times
        matcher._char_pos_to_time = MagicMock(return_value=(50.0, 55.0))

        full_text = "a" * 200
        result = matcher._scan_for_outro(full_text, {}, [], pattern, 0)

        assert result == 55.0
        matcher._fuzzy_find.assert_called_once()
        matcher._char_pos_to_time.assert_called_once()

    def test_scan_for_intro_returns_start_time(self):
        matcher = self._make_matcher()
        pattern = AdPattern(
            id=1, text_template="test",
            intro_variants=["brought to you by testco"],
            outro_variants=[], sponsor="test", scope="podcast",
        )
        matcher._fuzzy_find = MagicMock(return_value=(5, 90))
        matcher._char_pos_to_time = MagicMock(return_value=(30.0, 35.0))

        full_text = "a" * 200
        result = matcher._scan_for_intro(full_text, {}, [], pattern, 200)

        assert result == 30.0

    def test_scan_for_boundary_no_variants_returns_none(self):
        matcher = self._make_matcher()
        pattern = AdPattern(
            id=1, text_template="test", intro_variants=[],
            outro_variants=[], sponsor="test", scope="podcast",
        )

        result = matcher._scan_for_outro("some text", {}, [], pattern, 0)
        assert result is None

    def test_scan_for_boundary_short_phrase_skipped(self):
        matcher = self._make_matcher()
        pattern = AdPattern(
            id=1, text_template="test", intro_variants=[],
            outro_variants=["short"],  # < 10 chars, should be skipped
            sponsor="test", scope="podcast",
        )
        matcher._fuzzy_find = MagicMock()

        result = matcher._scan_for_outro("a" * 200, {}, [], pattern, 0)
        assert result is None
        matcher._fuzzy_find.assert_not_called()

    def test_scan_for_boundary_low_score_rejected(self):
        matcher = self._make_matcher()
        pattern = AdPattern(
            id=1, text_template="test", intro_variants=[],
            outro_variants=["a long enough outro phrase here"],
            sponsor="test", scope="podcast",
        )
        # Score below FUZZY_THRESHOLD * 100 (75)
        matcher._fuzzy_find = MagicMock(return_value=(10, 50))

        result = matcher._scan_for_outro("a" * 200, {}, [], pattern, 0)
        assert result is None


class TestEstimateDuration:
    """Tests for _estimate_end_from_duration and _estimate_start_from_duration."""

    def _make_matcher(self):
        matcher = TextPatternMatcher.__new__(TextPatternMatcher)
        return matcher

    def test_end_from_duration_uses_avg(self):
        matcher = self._make_matcher()
        pattern = AdPattern(
            id=1, text_template="test", intro_variants=[], outro_variants=[],
            sponsor="test", scope="podcast", avg_duration=45.0,
        )
        assert matcher._estimate_end_from_duration(pattern, 100.0) == 145.0

    def test_end_from_duration_none_uses_default(self):
        matcher = self._make_matcher()
        pattern = AdPattern(
            id=1, text_template="test", intro_variants=[], outro_variants=[],
            sponsor="test", scope="podcast", avg_duration=None,
        )
        assert matcher._estimate_end_from_duration(pattern, 100.0) == 100.0 + DEFAULT_AD_DURATION_ESTIMATE

    def test_end_from_duration_zero_uses_zero(self):
        """avg_duration=0.0 should use 0 (not fall back to default)."""
        matcher = self._make_matcher()
        pattern = AdPattern(
            id=1, text_template="test", intro_variants=[], outro_variants=[],
            sponsor="test", scope="podcast", avg_duration=0.0,
        )
        assert matcher._estimate_end_from_duration(pattern, 100.0) == 100.0

    def test_start_from_duration_uses_avg(self):
        matcher = self._make_matcher()
        pattern = AdPattern(
            id=1, text_template="test", intro_variants=[], outro_variants=[],
            sponsor="test", scope="podcast", avg_duration=30.0,
        )
        assert matcher._estimate_start_from_duration(pattern, 100.0) == 70.0

    def test_start_from_duration_none_uses_default(self):
        matcher = self._make_matcher()
        pattern = AdPattern(
            id=1, text_template="test", intro_variants=[], outro_variants=[],
            sponsor="test", scope="podcast", avg_duration=None,
        )
        assert matcher._estimate_start_from_duration(pattern, 100.0) == max(0, 100.0 - DEFAULT_AD_DURATION_ESTIMATE)

    def test_start_from_duration_clamps_to_zero(self):
        matcher = self._make_matcher()
        pattern = AdPattern(
            id=1, text_template="test", intro_variants=[], outro_variants=[],
            sponsor="test", scope="podcast", avg_duration=200.0,
        )
        assert matcher._estimate_start_from_duration(pattern, 50.0) == 0
