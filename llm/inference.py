"""
Real LLM provider wrapper for the project.

The final demo uses only providers we actually need:
- openai_compatible: Thunder Compute running vLLM/OpenAI-compatible API.
- ollama: local fallback, e.g. Hassan laptop running Ollama.
"""

import asyncio
import json
import logging
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Dict, Optional

import config

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


@dataclass
class LLMResult:
    text: str
    provider: str
    latency: float
    attempts: int


class LLMProviderError(RuntimeError):
    """Raised when the configured real LLM provider cannot complete a request."""


def build_prompt(query: str, context: str) -> str:
    return (
        "Answer the user request using the retrieved context when relevant. "
        "Keep the answer concise.\n\n"
        f"Retrieved context:\n{context}\n\n"
        f"User request:\n{query}\n\n"
        "Answer:"
    )


def _post_json(url: str, payload: Dict, headers: Dict[str, str], timeout: float) -> Dict:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response_body = response.read().decode("utf-8")
            return json.loads(response_body)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise LLMProviderError(f"HTTP {exc.code}: {detail[:300]}") from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise LLMProviderError(str(exc)) from exc


class LLMClient:
    def __init__(self, provider: Optional[str] = None):
        self.provider = (provider or config.LLM_PROVIDER).lower()
        if self.provider not in ("openai_compatible", "ollama"):
            raise LLMProviderError(
                "LLM_PROVIDER must be 'openai_compatible' for Thunder/vLLM "
                "or 'ollama' for local Ollama."
            )

    async def complete(self, query: str, context: str) -> LLMResult:
        prompt = build_prompt(query, context)
        last_error: Optional[Exception] = None
        start_time = time.perf_counter()

        for attempt in range(1, config.LLM_RETRIES + 2):
            try:
                if self.provider == "openai_compatible":
                    text = await self._openai_compatible(prompt)
                else:
                    text = await self._ollama(prompt)

                latency = time.perf_counter() - start_time
                logger.info(
                    "LLM provider=%s latency=%.3fs attempts=%s",
                    self.provider,
                    latency,
                    attempt,
                )
                return LLMResult(
                    text=text,
                    provider=self.provider,
                    latency=latency,
                    attempts=attempt,
                )
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "LLM provider=%s attempt=%s failed: %s",
                    self.provider,
                    attempt,
                    exc,
                )
                if attempt <= config.LLM_RETRIES:
                    await asyncio.sleep(0.25 * attempt)

        raise LLMProviderError(f"LLM request failed after retries: {last_error}")

    async def _openai_compatible(self, prompt: str) -> str:
        payload = {
            "model": config.OPENAI_COMPATIBLE_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": config.LLM_MAX_TOKENS,
            "temperature": 0.2,
        }
        headers = {
            "Authorization": f"Bearer {config.OPENAI_COMPATIBLE_API_KEY}",
            "Content-Type": "application/json",
        }
        url = f"{config.OPENAI_COMPATIBLE_BASE_URL.rstrip('/')}/chat/completions"
        data = await asyncio.wait_for(
            asyncio.to_thread(_post_json, url, payload, headers, config.LLM_TIMEOUT),
            timeout=config.LLM_TIMEOUT + 1,
        )
        return data["choices"][0]["message"]["content"].strip()

    async def _ollama(self, prompt: str) -> str:
        payload = {
            "model": config.OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": config.LLM_MAX_TOKENS, "temperature": 0.2},
        }
        headers = {"Content-Type": "application/json"}
        url = f"{config.OLLAMA_BASE_URL.rstrip('/')}/api/generate"
        data = await asyncio.wait_for(
            asyncio.to_thread(_post_json, url, payload, headers, config.LLM_TIMEOUT),
            timeout=config.LLM_TIMEOUT + 1,
        )
        return data.get("response", "").strip()


_default_client = LLMClient()


async def run_llm_async(query: str, context: str) -> LLMResult:
    return await _default_client.complete(query, context)


def run_llm(query: str, context: str) -> str:
    """Synchronous compatibility wrapper for older call sites."""
    return asyncio.run(run_llm_async(query, context)).text
