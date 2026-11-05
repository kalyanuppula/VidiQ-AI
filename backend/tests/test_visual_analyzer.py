import pytest
from types import SimpleNamespace
from app.services.multimodal import visual_analyzer
import os
from app.services.multimodal.visual_analyzer import analyze_frame


@pytest.mark.skipif(
    not os.getenv("RUN_GEMINI_TESTS"),
    reason="Set RUN_GEMINI_TESTS=1 to run Gemini integration tests",
)
def test_analyze_frame():
    result = analyze_frame(
        image_path="data/frames/vlm_test.jpeg",
        timestamp_seconds=15.0,
        video_id="test_video_001",
    )

    assert result["video_id"] == "test_video_001"
    assert result["timestamp_seconds"] == 15.0
    assert result["timestamp"] == "00:00:15"
    assert result["description"]
    assert result["model"]

    print("\nVisual Analysis Result")
    print("----------------------")

    for key, value in result.items():
        print(f"{key}: {value}")

def test_analyze_frame_success(tmp_path, monkeypatch):
    """Test successful frame analysis without calling Gemini."""

    image = tmp_path / "frame.jpg"
    image.write_bytes(b"fake-image-data")

    def fake_client():
        class FakeInteractions:
            def create(self, **kwargs):
                assert kwargs["model"] == visual_analyzer.MODEL_NAME
                assert kwargs["timeout"] == 90

                return SimpleNamespace(
                    output_text="A person is working at an industrial workstation."
                )

        return SimpleNamespace(
            interactions=FakeInteractions()
        )

    monkeypatch.setattr(
        visual_analyzer,
        "get_gemini_client",
        fake_client,
    )

    result = visual_analyzer.analyze_frame(
        image_path=image,
        timestamp_seconds=15.0,
        video_id="unit_test_001",
    )

    assert result["video_id"] == "unit_test_001"
    assert result["timestamp"] == "00:00:15"
    assert result["description"]
    assert result["model"] == visual_analyzer.MODEL_NAME


def test_missing_image():
    with pytest.raises(FileNotFoundError):
        visual_analyzer.analyze_frame(
            image_path="missing.jpg",
            timestamp_seconds=10,
        )


def test_unsupported_image_format(tmp_path):
    image = tmp_path / "frame.gif"
    image.write_bytes(b"test")

    with pytest.raises(ValueError, match="Unsupported image format"):
        visual_analyzer.analyze_frame(
            image_path=image,
            timestamp_seconds=10,
        )


def test_empty_image(tmp_path):
    image = tmp_path / "empty.jpg"
    image.write_bytes(b"")

    with pytest.raises(ValueError, match="Frame is empty"):
        visual_analyzer.analyze_frame(
            image_path=image,
            timestamp_seconds=10,
        )


def test_invalid_timestamp(tmp_path):
    image = tmp_path / "frame.jpg"
    image.write_bytes(b"fake-image-data")

    with pytest.raises(ValueError, match="Timestamp"):
        visual_analyzer.analyze_frame(
            image_path=image,
            timestamp_seconds=-5,
        )


def test_empty_gemini_response(tmp_path, monkeypatch):
    image = tmp_path / "frame.jpg"
    image.write_bytes(b"fake-image-data")

    class FakeInteractions:
        def create(self, **kwargs):
            return SimpleNamespace(output_text="")

    fake_client = SimpleNamespace(
        interactions=FakeInteractions()
    )

    monkeypatch.setattr(
        visual_analyzer,
        "get_gemini_client",
        lambda: fake_client,
    )

    with pytest.raises(RuntimeError, match="empty description"):
        visual_analyzer.analyze_frame(
            image_path=image,
            timestamp_seconds=10,
        )