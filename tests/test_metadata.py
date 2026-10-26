import unittest
import sys
import os
from pathlib import Path
from unittest.mock import patch
from mutagen import MutagenError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from metadata import extract_metadata  # noqa: E402


class TestMetadata(unittest.TestCase):
    @patch("metadata.EasyID3")
    def test_extract_metadata_success(self, mock_easyid3):
        mock_tags = {"artist": ["Test Artist"], "title": ["Test Title"], "album": ["Test Album"]}
        mock_easyid3.return_value = mock_tags

        mp3_path = Path("dummy_song.mp3")
        result = extract_metadata(mp3_path)

        self.assertEqual(result["artist"], "Test Artist")
        self.assertEqual(result["title"], "Test Title")
        self.assertEqual(result["album"], "Test Album")
        mock_easyid3.assert_called_once_with("dummy_song.mp3")

    @patch("metadata.EasyID3")
    def test_extract_metadata_missing_tags(self, mock_easyid3):
        mock_tags = {"artist": ["Test Artist"]}
        mock_easyid3.return_value = mock_tags

        mp3_path = Path("dummy_song.mp3")
        result = extract_metadata(mp3_path)

        self.assertEqual(result["artist"], "Test Artist")
        self.assertEqual(result["title"], "dummy_song")
        self.assertNotIn("album", result)

    @patch("builtins.print")
    @patch("metadata.EasyID3")
    def test_extract_metadata_exception(self, mock_easyid3, mock_print):
        mock_easyid3.side_effect = MutagenError("Read error")

        mp3_path = Path("dummy_song.mp3")
        result = extract_metadata(mp3_path)

        self.assertEqual(result["artist"], "Unknown")
        self.assertEqual(result["title"], "dummy_song")
        self.assertNotIn("album", result)
        mock_print.assert_called_once_with(
            "[metadata] Could not read tags from dummy_song.mp3: Read error"
        )


if __name__ == "__main__":
    unittest.main()
