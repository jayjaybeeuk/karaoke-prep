import unittest
import sys
import os
from pathlib import Path

# Add src directory to path to import pipeline
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from pipeline import lrc_to_ass, _seconds_to_ass, _escape_ffmpeg_path  # noqa: E402


def test_lrc_to_ass(tmp_path: Path):
    # Setup dummy LRC file
    lrc_content = "[01:05.12]Line 1\n" "[01:10.00]Line 2\n" "[01:15.00]"
    lrc_path = tmp_path / "test.lrc"
    lrc_path.write_text(lrc_content, encoding="utf-8")

    ass_path = tmp_path / "test.ass"

    # Run the conversion
    lrc_to_ass(lrc_path, ass_path)

    # Verify the output
    assert ass_path.exists()
    ass_content = ass_path.read_text(encoding="utf-8")

    # Assert headers
    assert "[Script Info]" in ass_content
    assert "[V4+ Styles]" in ass_content
    assert "[Events]" in ass_content

    # Assert events
    events = [line for line in ass_content.splitlines() if line.startswith("Dialogue:")]
    assert len(events) == 2, "Empty line should have been skipped in ASS events"

    # First event
    assert "0:01:05.12" in events[0]
    assert "0:01:10.00" in events[0]
    assert "Line 1" in events[0]

    # Second event
    assert "0:01:10.00" in events[1]
    assert "0:01:15.00" in events[1]
    assert "Line 2" in events[1]


class TestPipeline(unittest.TestCase):
    def test_seconds_to_ass(self):
        """Test conversion of seconds to ASS format h:mm:ss.cs"""
        test_cases = [
            (0.0, "0:00:00.00"),
            (0.5, "0:00:00.50"),
            (59.99, "0:00:59.99"),
            (60.0, "0:01:00.00"),
            (61.5, "0:01:01.50"),
            (3599.99, "0:59:59.99"),
            (3600.0, "1:00:00.00"),
            (3661.5, "1:01:01.50"),
            (36000.0, "10:00:00.00"),
            (3624.123, "1:00:24.12"),  # Rounding check
        ]

        for seconds, expected in test_cases:
            with self.subTest(seconds=seconds):
                self.assertEqual(_seconds_to_ass(seconds), expected)

    def test_escape_ffmpeg_path(self):
        """Test escaping of paths for FFmpeg filtergraph syntax."""
        test_cases = [
            # Normal paths
            ("normal/path/file.mp4", "normal/path/file.mp4"),
            ("path_with_underscore", "path_with_underscore"),
            # Characters that need first-level escaping only (not true, they all get second level)
            # Actually, `_escape_ffmpeg_path` applies two levels of escaping sequentially.
            # backslash -> double -> quad
            ("C:\\Windows\\Path", "C\\\\:\\\\\\\\Windows\\\\\\\\Path"),
            # : -> \: -> \\:
            ("path/with:colon", "path/with\\\\:colon"),
            # ' -> \' -> \\\'
            ("path/with'quote", "path/with\\\\\\'quote"),
            # , -> \,
            ("path/with,comma", "path/with\\,comma"),
            # ; -> \;
            ("path/with;semicolon", "path/with\\;semicolon"),
            # [ -> \[
            ("path/with[bracket", "path/with\\[bracket"),
            # ] -> \]
            ("path/with]bracket", "path/with\\]bracket"),
            # = -> \=
            ("path/with=equals", "path/with\\=equals"),
        ]

        for path, expected in test_cases:
            with self.subTest(path=path):
                self.assertEqual(_escape_ffmpeg_path(path), expected)


if __name__ == "__main__":
    unittest.main()
