"""Unit tests for auto_process_override serialization helpers in api.py."""
import pytest

from api import _serialize_auto_process, _deserialize_auto_process


class TestSerializeAutoProcess:
    def test_true_to_string(self):
        assert _serialize_auto_process(True) == 'true'

    def test_false_to_string(self):
        assert _serialize_auto_process(False) == 'false'

    def test_none_passthrough(self):
        assert _serialize_auto_process(None) is None

    def test_non_boolean_string_returns_none(self):
        assert _serialize_auto_process("yes") is None

    def test_int_returns_none(self):
        # int is not bool (even though bool is a subclass of int,
        # we use `is True` / `is False` identity checks)
        assert _serialize_auto_process(1) is None

    def test_zero_returns_none(self):
        assert _serialize_auto_process(0) is None


class TestDeserializeAutoProcess:
    def test_true_string_to_bool(self):
        assert _deserialize_auto_process('true') is True

    def test_false_string_to_bool(self):
        assert _deserialize_auto_process('false') is False

    def test_none_passthrough(self):
        assert _deserialize_auto_process(None) is None

    def test_empty_string_returns_none(self):
        assert _deserialize_auto_process('') is None

    def test_unexpected_string_returns_none(self):
        assert _deserialize_auto_process('yes') is None


class TestRoundtrip:
    @pytest.mark.parametrize("db_value", ['true', 'false'])
    def test_serialize_deserialize_roundtrip(self, db_value):
        api_value = _deserialize_auto_process(db_value)
        assert _serialize_auto_process(api_value) == db_value

    @pytest.mark.parametrize("api_value", [True, False])
    def test_deserialize_serialize_roundtrip(self, api_value):
        db_value = _serialize_auto_process(api_value)
        assert _deserialize_auto_process(db_value) is api_value
