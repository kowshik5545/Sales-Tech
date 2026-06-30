from __future__ import annotations

import json
from json import JSONDecodeError
import os
from typing import Any, Callable, TypeVar

from openai import OpenAI
from pydantic import ValidationError

T = TypeVar("T")


def get_litellm_client() -> OpenAI | None:
    base_url = os.getenv("LITELLM_PROXY_URL")
    api_key = os.getenv("LITELLM_VIRTUAL_KEY")
    if not base_url or not api_key:
        return None
    return OpenAI(base_url=f"{base_url.rstrip('/')}/v1", api_key=api_key)


def get_litellm_request_options() -> dict[str, Any]:
    headers: dict[str, str] = {}
    metadata: dict[str, str] = {}

    user_id = os.getenv("LITELLM_USER_ID")
    if user_id:
        headers["x-litellm-user-id"] = user_id

    department = os.getenv("LITELLM_DEPARTMENT")
    environment = os.getenv("LITELLM_ENVIRONMENT")
    if department:
        metadata["department"] = department
    if environment:
        metadata["environment"] = environment
    if metadata:
        headers["x-litellm-metadata"] = json.dumps(metadata)

    if not headers:
        return {}
    return {"extra_headers": headers}


def get_llm_model() -> str:
    return os.getenv("LITELLM_LLM_MODEL", "gpt-4o")


def get_stt_model() -> str:
    return os.getenv("LITELLM_STT_MODEL", "gpt-4o-mini-transcribe")


def get_whisper_model_name() -> str:
    return os.getenv("WHISPER_MODEL", "tiny")


def parse_json_response(raw_text: str) -> dict[str, Any]:
    return json.loads(raw_text)


def call_llm_json_with_retry(
    client: OpenAI,
    model: str,
    system_prompt: str,
    user_prompt: str,
    validator: Callable[[dict[str, Any]], T],
    temperature: float,
) -> T:
    prompt = user_prompt
    request_options = get_litellm_request_options()
    for attempt in range(2):
        response = client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            **request_options,
        )

        raw_content = response.choices[0].message.content or "{}"
        try:
            payload = parse_json_response(raw_content)
            return validator(payload)
        except (JSONDecodeError, ValidationError) as exc:
            if attempt == 1:
                raise
            prompt = (
                f"{user_prompt}\n\n"
                f"Your previous response was invalid. Error: {exc}. "
                "Return ONLY valid JSON matching the schema."
            )

    raise RuntimeError("LLM JSON call did not return a valid response")
