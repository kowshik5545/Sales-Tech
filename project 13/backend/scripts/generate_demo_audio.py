"""
Generate realistic voice recordings for the 5 demo sales call scenarios.
Uses gTTS for speech synthesis and pydub for audio assembly.

Usage:
    python scripts/generate_demo_audio.py

Output: frontend/public/audio/demo_call_1.wav through demo_call_5.wav
"""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from gtts import gTTS
from pydub import AudioSegment
from pydub.effects import normalize

from scripts.demo_dialogues import ALL_DIALOGUES  # noqa: E402


def silence(ms: int) -> AudioSegment:
    return AudioSegment.silent(duration=ms)


def speak(text: str, lang: str = "en", slow: bool = False) -> AudioSegment:
    tts = gTTS(text=text, lang=lang, slow=slow)
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        tts.save(f.name)
        audio = AudioSegment.from_mp3(f.name)
    os.unlink(f.name)
    return normalize(audio)


def build_conversation(dialogue: list[tuple[str, str]]) -> AudioSegment:
    audio = AudioSegment.empty()
    for i, (speaker, text) in enumerate(dialogue):
        line = speak(text)
        audio += line
        if i < len(dialogue) - 1:
            next_speaker = dialogue[i + 1][0]
            audio += silence(800 if next_speaker == "customer" else 500)
    return audio


def main():
    output_dir = Path(__file__).resolve().parent.parent.parent / "frontend" / "public" / "audio"
    output_dir.mkdir(parents=True, exist_ok=True)

    for idx, scenario in enumerate(ALL_DIALOGUES, start=1):
        filename = f"demo_call_{idx}.wav"
        dialogue = scenario["dialogue"]
        print(f"Generating {filename} — {scenario['name']} ({scenario['deal_stage']}) — {len(dialogue)} lines...")
        audio = build_conversation(dialogue)
        final = silence(2000) + audio + silence(1500)
        output_path = output_dir / filename
        final.export(str(output_path), format="wav", parameters=["-ar", "16000", "-ac", "1", "-sample_fmt", "s16"])
        duration_sec = len(final) / 1000
        print(f"  Saved: {output_path} ({duration_sec:.1f}s)")

    print(f"\nAll {len(ALL_DIALOGUES)} demo call recordings generated in {output_dir}")


if __name__ == "__main__":
    main()
