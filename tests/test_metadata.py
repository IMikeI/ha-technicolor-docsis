"""Validate shipped metadata and translations without Home Assistant."""

import ast
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
COMPONENT = ROOT / "custom_components/technicolor_docsis"


def leaf_paths(value, prefix=""):
    if not isinstance(value, dict):
        return {prefix}
    return set().union(*(leaf_paths(item, f"{prefix}.{key}") for key, item in value.items()))


class MetadataTests(unittest.TestCase):
    def test_metadata(self):
        manifest = json.loads((COMPONENT / "manifest.json").read_text())
        self.assertEqual(manifest["domain"], "technicolor_docsis")
        self.assertTrue(manifest["config_flow"])
        self.assertEqual(manifest["iot_class"], "local_polling")
        self.assertEqual(manifest["version"], "0.1.2")
        json.loads((ROOT / "hacs.json").read_text())

    def test_translations_match_and_cover_sensor_keys(self):
        strings = json.loads((COMPONENT / "strings.json").read_text())
        for language in ("en", "de"):
            translation = json.loads((COMPONENT / f"translations/{language}.json").read_text())
            self.assertEqual(leaf_paths(strings), leaf_paths(translation))
            for path in ("sensor.py", "binary_sensor.py"):
                tree = ast.parse((COMPONENT / path).read_text())
                keys = [
                    node.value.value
                    for node in ast.walk(tree)
                    if isinstance(node, ast.keyword) and node.arg == "translation_key"
                ]
                for key in keys:
                    self.assertIn(key, translation["entity"][path.removesuffix(".py")])

    def test_setup_notice_and_interval_translation(self):
        for language in ("en", "de"):
            translation = json.loads((COMPONENT / f"translations/{language}.json").read_text())
            notice = translation["config"]["step"]["user"]["description"]
            self.assertIn("CGA4233-EU", notice)
            self.assertIn("Salzburg AG", notice)
            self.assertIn("bridge", notice.lower())
            self.assertEqual(
                translation["entity"]["number"]["update_interval"]["name"],
                "Abfrageintervall" if language == "de" else "Update interval",
            )
