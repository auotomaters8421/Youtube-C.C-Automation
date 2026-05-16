import pytest
from unittest.mock import MagicMock, patch
from src.selector import select_topic, rank_shorts

def test_select_topic():
    # Mock data
    mock_videos = [
        {"title": "AI Automation News 1", "description": "Latest in AI automation..."},
        {"title": "Baking a Cake", "description": "How to bake a chocolate cake..."}
    ]
    
    # Expected viral topic
    expected_topic = "AI Automation News 1"
    
    # Path to mock: src.selector.genai.GenerativeModel
    with patch("src.selector.genai.GenerativeModel") as MockModel:
        mock_instance = MockModel.return_value
        mock_response = MagicMock()
        mock_response.text = expected_topic
        mock_instance.generate_content.return_value = mock_response
        
        result = select_topic(mock_videos)
        
        assert result == expected_topic
        MockModel.assert_called_once_with('gemini-2.5-flash')
        mock_instance.generate_content.assert_called_once()
        # Verify the prompt contains video info
        args, kwargs = mock_instance.generate_content.call_args
        prompt = args[0]
        assert "AI Automation News 1" in prompt
        assert "Baking a Cake" in prompt

def test_rank_shorts_velocity():
    current_time = 1700000000
    shorts_data = [
        {"video_id": "v1", "views": 1000, "upload_time": current_time - 3600}, # 1000/3600 = 0.27
        {"video_id": "v2", "views": 100, "upload_time": current_time - 60},    # 100/60 = 1.66
        {"video_id": "v3", "views": 5000, "upload_time": current_time - 36000} # 5000/36000 = 0.13
    ]
    
    with patch("time.time", return_value=current_time):
        ranked = rank_shorts(shorts_data)
        
    assert ranked[0]["video_id"] == "v2"
    assert ranked[1]["video_id"] == "v1"
    assert ranked[2]["video_id"] == "v3"

def test_rank_shorts_min_age():
    current_time = 1700000000
    shorts_data = [
        {"video_id": "v1", "views": 100, "upload_time": current_time}, # 0 seconds old
        {"video_id": "v2", "views": 50, "upload_time": current_time - 1} # 1 second old
    ]
    
    with patch("time.time", return_value=current_time):
        ranked = rank_shorts(shorts_data)
        
    # v1: 100 / 1 = 100
    # v2: 50 / 1 = 50
    assert ranked[0]["video_id"] == "v1"
    assert ranked[1]["video_id"] == "v2"
