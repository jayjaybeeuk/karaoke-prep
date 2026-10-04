import unittest
import sys
import os

# Add src directory to path to import pipeline
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from pipeline import _seconds_to_ass

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

if __name__ == '__main__':
    unittest.main()
