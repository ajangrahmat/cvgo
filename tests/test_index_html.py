"""Checks for the self-contained documentation page."""

import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).parents[1]
INDEX = ROOT / "index.html"
EXAMPLE_DIRS = (ROOT / "examples", ROOT / "examples" / "cli")


class DocumentationParser(HTMLParser):
    """Collect the structures that make code examples usable."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.copy_buttons = 0
        self.code_blocks = 0
        self.details = 0
        self.api_details = 0
        self.ids = []
        self.links = []
        self.python_blocks = []
        self._python_parts = None

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        classes = set(attributes.get("class", "").split())

        if "id" in attributes:
            self.ids.append(attributes["id"])

        href = attributes.get("href", "")

        if href.startswith("#"):
            self.links.append(href[1:])

        if tag == "details" and "example-card" in classes:
            self.details += 1

        if tag == "details" and "api-card" in classes:
            self.api_details += 1

        if tag == "button" and "data-copy" in attributes:
            self.copy_buttons += 1

        if tag == "code":
            if any(name.startswith("language-") for name in classes):
                self.code_blocks += 1
            if "language-python" in classes:
                self._python_parts = []

    def handle_data(self, data):
        if self._python_parts is not None:
            self._python_parts.append(data)

    def handle_endtag(self, tag):
        if tag == "code" and self._python_parts is not None:
            self.python_blocks.append("".join(self._python_parts))
            self._python_parts = None


class TestIndexHTML(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = INDEX.read_text(encoding="utf-8")
        cls.parser = DocumentationParser()
        cls.parser.feed(cls.source)

    def test_all_examples_are_complete_and_embedded(self):
        expected = []

        for directory in EXAMPLE_DIRS:
            expected.extend(
                path.read_text(encoding="utf-8").rstrip()
                for path in sorted(directory.glob("[0-9][0-9]_*.py"))
            )

        self.assertEqual(self.parser.details, 20)
        self.assertIn("40 complete, copy-ready examples.", self.source)
        for topic in ("telegram-person-security", "mqtt-robot", "websocket-robot"):
            self.assertIn(f'href="#{topic}"', self.source)
        self.assertGreaterEqual(len(self.parser.python_blocks), 40)
        self.assertEqual(
            self.parser.copy_buttons,
            self.parser.code_blocks,
        )

        def normalize_example(value):
            lines = value.strip().splitlines()
            indents = [
                len(line) - len(line.lstrip())
                for line in lines[1:]
                if line.strip()
            ]
            padding = min(indents, default=0)
            return "\n".join(
                line if index == 0 else line[padding:]
                for index, line in enumerate(lines)
            )

        embedded = [normalize_example(block) for block in self.parser.python_blocks]
        for example in expected:
            self.assertIn(normalize_example(example), embedded)

    def test_advanced_parameters_are_complete_and_copyable(self):
        self.assertEqual(self.parser.api_details, 10)

        required_sections = {
            "advanced",
            "parameters-camera",
            "parameters-face",
            "parameters-hand",
            "parameters-pose",
            "parameters-holistic",
            "parameters-object",
            "parameters-gesture",
            "parameters-utilities",
            "parameters-output",
            "parameters-driver",
        }
        self.assertTrue(required_sections.issubset(self.parser.ids))

        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        documented_parameters = (
            "backend",
            "engine",
            "detection_confidence",
            "tracking_confidence",
            "model_complexity",
            "min_visibility",
            "gesture_confidence",
            "presence_confidence",
            "reconnect_after",
            "settle_time",
            "send_photo_async",
            "missing_alert_after",
            "serial_repeat_after",
        )

        for parameter in documented_parameters:
            with self.subTest(parameter=parameter):
                self.assertIn(parameter, self.source)
                self.assertIn(parameter, readme)

    def test_copy_and_keyboard_controls_are_present(self):
        self.assertIn("navigator.clipboard.writeText", self.source)
        self.assertIn('document.execCommand("copy")', self.source)
        self.assertIn('target.matches("details")', self.source)
        self.assertIn('"ArrowLeft"', self.source)
        self.assertIn('"ArrowRight"', self.source)

    def test_ids_are_unique_and_internal_links_have_targets(self):
        self.assertEqual(len(self.parser.ids), len(set(self.parser.ids)))

        targets = set(self.parser.ids)

        for link in self.parser.links:
            with self.subTest(link=link):
                self.assertIn(link, targets)

    def test_version_and_diagnostics_are_current(self):
        self.assertIn("CVGO 0.3.0", self.source)
        self.assertIn("python -m cvgo check --camera 4", self.source)
        self.assertNotIn("CVGO 0.2.0", self.source)


if __name__ == "__main__":
    unittest.main()
