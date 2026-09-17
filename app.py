import os
import json
import argparse
import subprocess
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OUTPUT = Path("output")
OUTPUT.mkdir(exist_ok=True)


def create_video_package(topic):
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    prompt = f"""
आप एक Hindi YouTube content creator हैं।

Topic: {topic}

इस topic पर एक आकर्षक YouTube वीडियो तैयार करें।

केवल valid JSON में जवाब दें:

{{
  "title": "YouTube title",
  "description": "पूरी description",
  "tags": ["tag1", "tag2", "tag3"],
  "script": "पूरा Hindi narration script"
}}

नियम:
- आसान और natural Hindi
- वीडियो लगभग 3 से 5 मिनट का हो
- शुरुआत में strong hook हो
- जानकारी स्पष्ट तरीके से समझाएं
- अंत में छोटा conclusion और subscribe call-to-action दें
- झूठी या मनगढ़ंत जानकारी न दें
- Title 100 characters से छोटा रखें
"""

    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-5.6-mini"),
        input=prompt
    )

    text = response.output_text.strip()

    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0]

    return json.loads(text)


def create_voice():
    subprocess.run(
        [
            "edge-tts",
            "--voice",
            os.getenv("TTS_VOICE", "hi-IN-MadhurNeural"),
            "--file",
            "output/script.txt",
            "--write-media",
            "output/voice.mp3"
        ],
        check=True
    )


def create_video():
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=black:s=1280x720:r=30",
            "-i",
            "output/voice.mp3",
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            "-pix_fmt",
            "yuv420p",
            "-shortest",
            "output/video.mp4"
        ],
        check=True
    )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--topic",
        required=True,
        help="Video topic"
    )

    parser.add_argument(
        "--make-video",
        action="store_true"
    )

    args = parser.parse_args()

    print("AI content बना रहा है...")

    data = create_video_package(args.topic)

    Path("output/package.json").write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    Path("output/script.txt").write_text(
        data["script"],
        encoding="utf-8"
    )

    print("\nTITLE:")
    print(data["title"])

    print("\nDESCRIPTION:")
    print(data["description"])

    print("\nTAGS:")
    print(", ".join(data["tags"]))

    print("\nSCRIPT तैयार है।")

    if args.make_video:
        print("\nAI voice बना रहा है...")
        create_voice()

        print("Video बना रहा है...")
        create_video()

        print("\nVideo तैयार है:")
        print("output/video.mp4")


if __name__ == "__main__":
    main()
