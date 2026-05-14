import os
import json
import pytest
from unittest.mock import patch, MagicMock
from src.watcher import check_for_new_videos

@patch("src.watcher.fetch_feed")
@patch("src.watcher.Config")
def test_check_for_new_videos_returns_only_new(mock_config, mock_fetch, tmp_path):
    # Setup paths
    data_dir = tmp_path / "data"
    data_dir.mkdir(exist_ok=True)
    seen_file = data_dir / "seen_videos.json"
    seen_file.write_text(json.dumps(["video1"]))
    
    # Mock Config
    mock_config.CHANNELS = ["channel1"]
    
    # Mock fetch_feed
    mock_fetch.return_value = [
        MagicMock(id="video1", title="Title 1", link="Link 1"),
        MagicMock(id="video2", title="Title 2", link="Link 2")
    ]
    
    new_videos = check_for_new_videos(seen_file_path=str(seen_file))
    
    assert len(new_videos) == 1
    assert new_videos[0]["id"] == "video2"
    assert new_videos[0]["title"] == "Title 2"
    
    # Verify persistence
    with open(seen_file, "r") as f:
        seen_list = json.load(f)
    assert "video1" in seen_list
    assert "video2" in seen_list

@patch("src.watcher.fetch_feed")
@patch("src.watcher.Config")
def test_check_for_new_videos_handles_empty_channels(mock_config, mock_fetch, tmp_path):
    seen_file = tmp_path / "seen_videos.json"
    mock_config.CHANNELS = []
    
    new_videos = check_for_new_videos(seen_file_path=str(seen_file))
    
    assert len(new_videos) == 0
    mock_fetch.assert_not_called()
