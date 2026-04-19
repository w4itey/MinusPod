"""Tests for chapters_generator topic-boundary prompt construction."""
import os
import sys
from dataclasses import dataclass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from chapters_generator import ChaptersGenerator


@dataclass
class _StubResponse:
    content: str
    model: str = 'stub-model'
    usage: dict = None
    raw_response: object = None


class _RecordingClient:
    """Stub LLM client that records every prompt it was asked to send."""

    def __init__(self, canned_text: str = ''):
        self.canned_text = canned_text
        self.prompts: list = []

    def messages_create(self, **kwargs):
        self.prompts.append(kwargs['messages'][0]['content'])
        return _StubResponse(content=self.canned_text)

    @property
    def last_prompt(self) -> str:
        return self.prompts[-1] if self.prompts else ''

    @property
    def topic_prompt(self) -> str:
        """Return the first prompt (topic-detection), raising if absent."""
        for p in self.prompts:
            if 'identify' in p and 'major topic changes' in p:
                return p
        return ''


def _make_generator_with_stub(canned_text: str = '') -> tuple:
    gen = ChaptersGenerator(api_key='test')
    stub = _RecordingClient(canned_text=canned_text)
    gen._llm_client = stub
    return gen, stub


class TestDetectTopicBoundariesPromptSize:
    """Full transcript must reach the LLM (no 8,000-char cap)."""

    def test_long_transcript_not_truncated(self):
        # 40,000 chars of transcript with a unique marker well past the 8k mark.
        filler_before = 'a ' * 6000  # 12,000 chars
        marker = '[TAIL_MARKER_XYZ]'
        filler_after = 'b ' * 10000  # 20,000 chars
        transcript = f'[00:00] start\n{filler_before}\n[60:00] {marker}\n{filler_after}'
        assert len(transcript) > 8000

        gen, stub = _make_generator_with_stub(canned_text='')
        gen._detect_topic_boundaries(
            transcript=transcript,
            start_time=0.0,
            end_time=7200.0,
            num_splits=6,
        )

        assert marker in stub.last_prompt, (
            'Marker past byte 8000 must appear in the prompt; '
            'otherwise transcript is being truncated.'
        )
        assert transcript in stub.last_prompt, (
            'Full transcript must appear verbatim in the prompt.'
        )

    def test_num_splits_reaches_prompt(self):
        gen, stub = _make_generator_with_stub(canned_text='')
        gen._detect_topic_boundaries(
            transcript='[00:00] hello world',
            start_time=0.0,
            end_time=120.0,
            num_splits=4,
        )
        assert 'identify 4 major topic changes' in stub.last_prompt


class TestDetectTopicBoundariesParsing:
    """LLM output parsing: valid MM:SS lines become chapters, noise is dropped."""

    def test_parses_mmss_lines_within_range(self):
        canned = "05:30 Opening segment\n45:00 Guest interview\n90:15 Closing\n"
        gen, _ = _make_generator_with_stub(canned_text=canned)
        chapters = gen._detect_topic_boundaries(
            transcript='[00:00] x',
            start_time=0.0,
            end_time=7200.0,
            num_splits=3,
        )
        assert [c['title'] for c in chapters] == [
            'Opening segment', 'Guest interview', 'Closing',
        ]
        assert [int(c['original_time']) for c in chapters] == [330, 2700, 5415]

    def test_rejects_timestamps_outside_range(self):
        canned = "05:30 Inside\n99:99 garbage\n200:00 Outside\n"
        gen, _ = _make_generator_with_stub(canned_text=canned)
        chapters = gen._detect_topic_boundaries(
            transcript='[00:00] x',
            start_time=0.0,
            end_time=1800.0,
            num_splits=3,
        )
        assert [c['title'] for c in chapters] == ['Inside']


class TestDetectTopicBoundariesDescription:
    """Episode description is injected into the prompt with an ordering instruction."""

    def test_description_reaches_prompt_when_provided(self):
        gen, stub = _make_generator_with_stub(canned_text='')
        gen._detect_topic_boundaries(
            transcript='[00:00] x',
            start_time=0.0,
            end_time=1800.0,
            num_splits=3,
            episode_description='00:00 Intro\n05:30 Main\n15:00 Guest',
        )
        assert '00:00 Intro' in stub.last_prompt
        assert '15:00 Guest' in stub.last_prompt
        assert 'prefer those timestamps' in stub.last_prompt

    def test_no_description_block_when_empty(self):
        gen, stub = _make_generator_with_stub(canned_text='')
        gen._detect_topic_boundaries(
            transcript='[00:00] x',
            start_time=0.0,
            end_time=1800.0,
            num_splits=3,
            episode_description=None,
        )
        assert 'Episode description' not in stub.last_prompt
        assert 'prefer those timestamps' not in stub.last_prompt

    def test_whitespace_only_description_is_ignored(self):
        gen, stub = _make_generator_with_stub(canned_text='')
        gen._detect_topic_boundaries(
            transcript='[00:00] x',
            start_time=0.0,
            end_time=1800.0,
            num_splits=3,
            episode_description='   \n\t  ',
        )
        assert 'Episode description' not in stub.last_prompt


class TestAdjustSegmentsForAds:
    """Raw segments + ads_removed must project onto the post-ad-removal timeline."""

    def test_no_ads_returns_segments_unchanged(self):
        gen = ChaptersGenerator(api_key='test')
        segs = [{'start': 0, 'end': 10, 'text': 'a'},
                {'start': 10, 'end': 20, 'text': 'b'}]
        assert gen._adjust_segments_for_ads(segs, []) == segs
        assert gen._adjust_segments_for_ads(segs, None) == segs

    def test_drops_segments_entirely_inside_ad(self):
        gen = ChaptersGenerator(api_key='test')
        segs = [
            {'start': 0, 'end': 10, 'text': 'before'},
            {'start': 15, 'end': 25, 'text': 'inside-ad'},
            {'start': 40, 'end': 50, 'text': 'after'},
        ]
        ads = [{'start': 10, 'end': 30}]
        out = gen._adjust_segments_for_ads(segs, ads)
        texts = [s['text'] for s in out]
        assert 'inside-ad' not in texts
        assert texts == ['before', 'after']

    def test_shifts_post_ad_segments_by_ad_duration(self):
        gen = ChaptersGenerator(api_key='test')
        segs = [
            {'start': 0, 'end': 10, 'text': 'before'},
            {'start': 40, 'end': 50, 'text': 'after'},
        ]
        ads = [{'start': 10, 'end': 30}]
        out = gen._adjust_segments_for_ads(segs, ads)
        assert out[0]['start'] == 0 and out[0]['end'] == 10
        assert out[1]['start'] == 20 and out[1]['end'] == 30


class TestGenerateChaptersUnifiedEntryPoint:
    """Both pipeline and regen call the same method and get the same shape."""

    def _segments(self, duration: int = 1200):
        """Build a synthetic segment list covering `duration` seconds with enough text."""
        return [
            {'start': i, 'end': i + 10,
             'text': f'segment {i} with enough words to exceed the five hundred char gate a b c d e f g'}
            for i in range(0, duration, 10)
        ]

    def test_empty_segments_returns_empty_chapters(self):
        gen, _ = _make_generator_with_stub(canned_text='')
        out = gen.generate_chapters([])
        assert out == {'version': '1.2.0', 'chapters': []}

    def test_regen_path_no_ads_removed(self):
        gen, stub = _make_generator_with_stub(canned_text='10:00 Middle section\n')
        segs = self._segments(duration=1800)
        out = gen.generate_chapters(
            segments=segs,
            episode_description=None,
            podcast_name='Show',
            episode_title='Ep',
        )
        assert out['version'] == '1.2.0'
        assert len(out['chapters']) >= 1
        assert 'Transcript:' in stub.topic_prompt

    def test_pipeline_path_applies_ad_adjustment(self):
        gen, stub = _make_generator_with_stub(canned_text='')
        # Build enough segments so the post-adjustment transcript exceeds the
        # 500-char gate and _detect_topic_boundaries actually runs.
        text_filler = 'words ' * 20  # 120 chars/segment
        segs = [
            {'start': i, 'end': i + 10, 'text': f'pre {text_filler}'}
            for i in range(0, 500, 10)
        ] + [
            {'start': 500, 'end': 560, 'text': 'ad body should be dropped'},
        ] + [
            {'start': i, 'end': i + 10, 'text': f'post {text_filler}'}
            for i in range(560, 1400, 10)
        ]
        ads = [{'start': 500, 'end': 560}]
        gen.generate_chapters(
            segments=segs,
            ads_removed=ads,
            podcast_name='Show',
            episode_title='Ep',
        )
        topic_prompt = stub.topic_prompt
        assert topic_prompt, 'Topic-detection prompt must have been sent'
        # Post-adjustment: the segment originally at 560 should now start at 500 (08:20).
        assert '[08:20] post' in topic_prompt
        assert 'ad body should be dropped' not in topic_prompt
