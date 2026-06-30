from __future__ import annotations

from types import SimpleNamespace


class FakeCompletions:
    def __init__(self, outputs: list[str]):
        self.outputs = outputs
        self.call_count = 0

    def create(self, **kwargs):  # noqa: ANN003
        index = min(self.call_count, len(self.outputs) - 1)
        self.call_count += 1
        content = self.outputs[index]
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
        )


class FakeChat:
    def __init__(self, outputs: list[str]):
        self.completions = FakeCompletions(outputs)


class FakeLLMClient:
    def __init__(self, outputs: list[str]):
        self.chat = FakeChat(outputs)


class FakeTranscriptionEndpoint:
    def __init__(self, payload):
        self.payload = payload
        self.call_count = 0

    def create(self, **kwargs):  # noqa: ANN003
        self.call_count += 1
        return self.payload


class FakeAudio:
    def __init__(self, payload):
        self.transcriptions = FakeTranscriptionEndpoint(payload)


class FakeSTTClient:
    def __init__(self, payload):
        self.audio = FakeAudio(payload)
