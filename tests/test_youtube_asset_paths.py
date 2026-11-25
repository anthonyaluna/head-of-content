from importlib.util import module_from_spec, spec_from_file_location
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

import pytest


SCRIPT = Path(__file__).parents[1] / ".claude/skills/youtube-research/scripts/find_outliers.py"
spec = spec_from_file_location("find_outliers", SCRIPT)
research = module_from_spec(spec)
spec.loader.exec_module(research)
VIDEO_ID = "Yt_Ab-12345"


def video(video_id):
    return {"id": video_id, "snippet": {"thumbnails": {"high": {"url": "https://example.invalid/thumbnail"}}}}


@pytest.mark.parametrize("value", [None, 42, "", "short", "video 12345", "émissions01", "a" * 12])
def test_invalid_ids_do_not_request_or_write(value, tmp_path):
    with patch.object(research, "urlopen") as fetch:
        assert research.download_thumbnail(video(value), tmp_path) is None
        assert research.fetch_transcript(value, "fixture", tmp_path) is None
    fetch.assert_not_called()
    assert list(tmp_path.iterdir()) == []


def test_valid_assets_can_be_refreshed(tmp_path):
    with patch.object(research, "urlopen", side_effect=[BytesIO(b"image"), BytesIO(b"updated"), BytesIO(b'{"segments":[{"text":"test"}]}')]):
        thumb = Path(research.download_thumbnail(video(VIDEO_ID), tmp_path))
        assert thumb.read_bytes() == b"image"
        assert Path(research.download_thumbnail(video(VIDEO_ID), tmp_path)) == thumb
        assert thumb.read_bytes() == b"updated"
        transcript = Path(research.fetch_transcript(VIDEO_ID, "fixture", tmp_path))
        assert transcript.read_text() == "[00:00] test"
    assert {p.name for p in tmp_path.iterdir()} == {VIDEO_ID + ".jpg", VIDEO_ID + ".txt"}


def test_search_filters_malformed_records():
    body = b'{"hits":[{"id":"Yt_Ab-12345"},{"id":"short"},null,{}]}'
    with patch.object(research, "urlopen", return_value=BytesIO(body)):
        assert research.search_outliers(["example"], "fixture") == [{"id": VIDEO_ID}]


def test_existing_symbolic_link_is_skipped(tmp_path):
    target = tmp_path / "existing"
    target.write_bytes(b"existing")
    try:
        (tmp_path / (VIDEO_ID + ".jpg")).symlink_to(target)
    except OSError:
        pytest.skip("Creating a symbolic link is unavailable on this host")
    with patch.object(research, "urlopen") as fetch:
        assert research.download_thumbnail(video(VIDEO_ID), tmp_path) is None
    fetch.assert_not_called()
    assert target.read_bytes() == b"existing"


def test_link_check_precedes_network_access_on_all_platforms(tmp_path):
    with patch.object(Path, "is_symlink", return_value=True), patch.object(research, "urlopen") as fetch:
        assert research.fetch_transcript(VIDEO_ID, "fixture", tmp_path) is None
        assert research.download_thumbnail(video(VIDEO_ID), tmp_path) is None
    fetch.assert_not_called()
