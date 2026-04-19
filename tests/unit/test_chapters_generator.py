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
    """Stub LLM client that records the last prompt it was asked to send."""

    def __init__(self, canned_text: str = ''):
        self.canned_text = canned_text
        self.last_prompt: str = ''

    def messages_create(self, **kwargs):
        self.last_prompt = kwargs['messages'][0]['content']
        return _StubResponse(content=self.canned_text)


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
