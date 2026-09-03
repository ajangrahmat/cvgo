"""Static checks for terminal-only examples."""

import ast
import unittest
from pathlib import Path


CLI_DIR = Path(__file__).parents[1] / "examples" / "cli"
EXPECTED_EXAMPLES = {
    f"{number:02d}_{name}.py"
    for number, name in enumerate(
        (
            "camera",
            "face_detection",
            "face_landmarks",
            "face_metrics",
            "serial_arduino",
            "face_to_arduino",
            "drowsiness",
            "driver_monitor",
            "hand_tracking",
            "pose_tracking",
            "security_pose",
            "object_detection",
            "person_security",
            "gesture_recognition",
            "holistic_tracking",
            "selfie_segmentation",
            "telegram_security",
        ),
        start=1,
    )
}


class TestCLIExamples(unittest.TestCase):
    def test_all_topics_have_a_cli_example(self):
        actual = {path.name for path in CLI_DIR.glob("*.py")}
        self.assertEqual(actual, EXPECTED_EXAMPLES)

    def test_examples_are_valid_python_without_gui_calls(self):
        forbidden = ("camera.show(", ".draw(", "go.put_text(")

        for path in CLI_DIR.glob("*.py"):
            with self.subTest(path=path.name):
                source = path.read_text(encoding="utf-8")
                ast.parse(source, filename=str(path))

                for call in forbidden:
                    self.assertNotIn(call, source)
