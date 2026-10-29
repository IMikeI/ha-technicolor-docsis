"""Measurement conversion and deliberately separate error-slot identities."""

import importlib.util
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "router_data",
    Path(__file__).parents[1] / "custom_components/technicolor_docsis/data.py",
)
data = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(data)


class DataTests(unittest.TestCase):
    def test_numeric_measurements(self):
        for raw, unit, expected in (
            ("-2.9 dBmV", "dBmV", -2.9),
            ("42.67 dB", "dB", 42.67),
            ("122 MHz", "MHz", 122),
            ("122000000 Hz", "MHz", 122),
            ("0.122 GHz", "MHz", 122),
            ("5120000", "Bd", 5120000),
            ("18446744073709551615", None, 18446744073709551615),
        ):
            with self.subTest(raw=raw):
                self.assertEqual(data.number(raw, unit), expected)

    def test_unknown_values_are_not_zero(self):
        for raw in (None, "NA", "N/A", "", "nan", "inf", "64-QAM", True):
            with self.subTest(raw=raw):
                self.assertIsNone(data.number(raw))
        self.assertIsNone(data.number("42 dB", "dBmV"))

    def test_error_slots_are_not_assigned_channel_ids(self):
        row = {"__id": "1", "ChannelID": "159"}
        self.assertEqual(data.row_identity("ErrTbl", row), "1")
        self.assertEqual(data.row_identity("exDSTbl", row), "159")

    def test_missing_channel_and_reordering(self):
        snapshot = {"modem": {"DSTbl": [{"ChannelID": "2"}, {"ChannelID": "1"}]}}
        self.assertEqual(data.find_row(snapshot, "DSTbl", "1"), {"ChannelID": "1"})
        self.assertIsNone(data.find_row(snapshot, "DSTbl", "3"))
