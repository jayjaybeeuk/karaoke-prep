import pytest
from pathlib import Path
from pipeline import lrc_to_ass

def test_lrc_to_ass(tmp_path: Path):
    # Setup dummy LRC file
    lrc_content = (
        "[01:05.12]Line 1\n"
        "[01:10.00]Line 2\n"
        "[01:15.00]"
    )
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
