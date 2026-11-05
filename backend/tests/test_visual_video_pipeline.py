import pytest
import os

os.environ.setdefault("PYDANTIC_DISABLE_PLUGINS", "__all__")

from app.services.video_processing.video_pipeline import process_video
from app.services.multimodal.visual_pipeline import analyze_video_frames


@pytest.mark.skipif(
    not os.getenv("RUN_GEMINI_TESTS"),
    reason="Set RUN_GEMINI_TESTS=1 to run Gemini integration tests",
)
def test_visual_video_pipeline():

    # Step 1: Process the video.
    video_result = process_video(
        video_path="data/raw_videos/visual_test.mp4",
        data_dir="data",
        interval_seconds=5,
    )

    assert video_result["status"] == "completed"
    assert video_result["frames"]["total_frames"] > 0

    # Step 2: Analyze extracted frames.
    analysis_result = analyze_video_frames(
        manifest_path="data/frames/visual_test/frames_manifest.json",
        video_id="visual_test_001",
    )

    assert analysis_result["status"] == "completed"
    assert analysis_result["total_frames_analyzed"] > 0
    assert analysis_result["total_frames_failed"] == 0

    print("\n===== FINAL SUMMARY =====")
    print("Video ID:", analysis_result["video_id"])
    print("Frames analyzed:", analysis_result["total_frames_analyzed"])

    for item in analysis_result["visual_descriptions"]:
        print("\nTimestamp:", item["timestamp"])
        print("Description:", item["description"])