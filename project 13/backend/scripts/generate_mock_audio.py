from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

SAMPLE_RATE = 16_000


def write_wav(path: Path, segments: list[tuple[str, float, float, float]]) -> None:
    frames: list[bytes] = []
    for kind, duration, frequency, amplitude in segments:
        sample_count = int(SAMPLE_RATE * duration)
        for i in range(sample_count):
            if kind == "tone":
                sample = int(amplitude * 32767 * math.sin(2 * math.pi * frequency * i / SAMPLE_RATE))
            else:
                sample = 0
            frames.append(struct.pack("<h", sample))

    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(b"".join(frames))


def main() -> None:
    output_dir = Path(__file__).resolve().parents[2] / "mock_data"
    output_dir.mkdir(parents=True, exist_ok=True)

    write_wav(
        output_dir / "sample_call_1.wav",
        [
            ("tone", 1.5, 440.0, 0.18),
            ("silence", 0.3, 0.0, 0.0),
            ("tone", 1.2, 660.0, 0.14),
            ("silence", 0.3, 0.0, 0.0),
            ("tone", 1.0, 520.0, 0.16),
        ],
    )
    write_wav(
        output_dir / "sample_call_2.wav",
        [
            ("tone", 1.0, 330.0, 0.20),
            ("silence", 0.4, 0.0, 0.0),
            ("tone", 1.0, 550.0, 0.15),
            ("silence", 0.4, 0.0, 0.0),
            ("tone", 1.3, 770.0, 0.12),
        ],
    )

    for file_name in ["sample_call_1.wav", "sample_call_2.wav"]:
        file_path = output_dir / file_name
        print(f"{file_name} -> {file_path.stat().st_size} bytes")


if __name__ == "__main__":
    main()
