from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "run_unified_demo", ROOT / "scripts" / "run_unified_demo.py"
)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class UnifiedDemoRunnerTests(unittest.TestCase):
    def test_default_artifacts_preserve_the_frozen_demo_paths(self):
        self.assertEqual(
            runner.artifact_paths(None),
            (runner.METRICS_FILE, runner.REPLAY_FILE, runner.ATTEMPT_FILE),
        )

    def test_suffix_creates_separate_metrics_replay_and_attempt_artifacts(self):
        paths = runner.artifact_paths("hardened_medium_20261029")
        self.assertEqual(
            [path.name for path in paths],
            [
                "unified_demo_metrics_hardened_medium_20261029.json",
                "unified_demo_replay_hardened_medium_20261029.json",
                "unified_demo_attempt_hardened_medium_20261029.json",
            ],
        )
        self.assertTrue(all(path.parent == ROOT / "calibration" for path in paths))

    def test_invalid_suffix_is_rejected_before_a_live_run(self):
        for suffix in ("../overwrite", "", "spaces are bad", ".hidden"):
            with self.subTest(suffix=suffix), self.assertRaises(ValueError):
                runner.artifact_paths(suffix)

    def test_v3_keyword_only_fixture_has_no_concrete_duty_example(self):
        fixture_path = ROOT / "calibration" / "unified_supplier_operations_demo_20261029_v3.json"
        fixture = runner.load_fixture(fixture_path)
        candidate = next(
            item for item in fixture["candidates"] if item["id"] == "unified_c2_keyword_only"
        )

        self.assertNotIn("Processed purchase-order changes", candidate["cv_pages"][0])
        self.assertEqual(
            [(item["evidence_type"], item["evidence_strength"]) for item in candidate["expected"]],
            [("unsupported", "keyword_only"), ("unsupported", "keyword_only")],
        )

    def test_fixture_path_must_remain_under_calibration(self):
        for path in ("../outside.json", "/tmp/outside.json"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                runner.resolve_fixture_path(path)


if __name__ == "__main__":
    unittest.main()
