import pytest
from dotenv import load_dotenv

import os
os.environ.setdefault("PYDANTIC_DISABLE_PLUGINS", "__all__")

import base64
from pathlib import Path
from google import genai


# Work around slow Pydantic plugin discovery.
os.environ.setdefault("PYDANTIC_DISABLE_PLUGINS", "__all__")

load_dotenv("backend/.env")


@pytest.mark.skipif(
    not os.getenv("RUN_GEMINI_TESTS"),
    reason="Set RUN_GEMINI_TESTS=1 to run Gemini integration tests",
)
def test_gemini_vision():

    api_key = os.getenv("GEMINI_API_KEY")

    assert api_key, "GEMINI_API_KEY not found in backend/.env"

    image_path = Path("data/frames/vlm_test.jpeg")

    assert image_path.exists(), f"Image not found: {image_path}"

    image_bytes = image_path.read_bytes()
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    client = genai.Client(api_key=api_key)

    interaction = client.interactions.create(
        model="gemini-3.5-flash-lite",
        input=[
            {
                "type": "text",
                "text": (
                    "Describe the visible objects, people, activities, "
                    "equipment and readable text. Only report details "
                    "that are clearly visible."
                ),
            },
            {
                "type": "image",
                "data": image_base64,
                "mime_type": "image/jpeg",
            },
        ],
    )

    assert interaction.output_text
    print("\nGemini Vision Response:\n")
    print(interaction.output_text)