"""
Async LLM provider wrapper.

The system supports real free/low-cost providers:
- OpenRouter chat completions when OPENROUTER_API_KEY is configured.
- HuggingFace Inference API when HUGGINGFACE_API_KEY is configured.
- Local Ollama when LLM_PROVIDER=ollama.

For classroom load tests without credentials, ALLOW_SIMULATED_LLM keeps the
distributed pipeline runnable while clearly marking responses as simulated.
Set ALLOW_SIMULATED_LLM=false to require a real provider.
"""

import asyncio
import json
import logging
import random
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Dict, List, Optional

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
    """Raised when an LLM provider cannot complete a request."""


def build_prompt(query: str, context: str) -> str:
    return (
        "You are serving a distributed systems project demo. Answer using the "
        "retrieved context when it is relevant.\n\n"
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

    def _candidate_providers(self) -> List[str]:
        if self.provider != "auto":
            return [self.provider]

        candidates: List[str] = []
        if config.OPENROUTER_API_KEY:
            candidates.append("openrouter")
        if config.HUGGINGFACE_API_KEY:
            candidates.append("huggingface")
        if "ollama" in config.OLLAMA_BASE_URL.lower() and config.OLLAMA_MODEL:
            # Ollama is only tried automatically when explicitly enabled by URL/model.
            if config.OLLAMA_BASE_URL != "http://localhost:11434":
                candidates.append("ollama")
        if not candidates and config.ALLOW_SIMULATED_LLM:
            candidates.append("simulated")
        return candidates

    async def complete(self, query: str, context: str) -> LLMResult:
        prompt = build_prompt(query, context)
        provider_errors: List[str] = []

        for provider in self._candidate_providers():
            try:
                return await self._complete_with_retries(provider, prompt, query, context)
            except LLMProviderError as exc:
                provider_errors.append(f"{provider}: {exc}")
                logger.warning("Provider %s failed: %s", provider, exc)

        if config.ALLOW_SIMULATED_LLM and self.provider != "simulated":
            return await self._complete_with_retries("simulated", prompt, query, context)

        error_text = "; ".join(provider_errors) or "no provider configured"
        raise LLMProviderError(f"LLM request failed: {error_text}")

    async def _complete_with_retries(
        self,
        provider: str,
        prompt: str,
        query: str,
        context: str,
    ) -> LLMResult:
        last_error: Optional[Exception] = None
        start_time = time.perf_counter()

        for attempt in range(1, config.LLM_RETRIES + 2):
            try:
                if provider == "openrouter":
                    text = await self._openrouter(prompt)
                elif provider == "huggingface":
                    text = await self._huggingface(prompt)
                elif provider == "ollama":
                    text = await self._ollama(prompt)
                elif provider == "simulated":
                    text = await self._simulated(query, context)
                else:
                    raise LLMProviderError(f"unknown provider '{provider}'")

                latency = time.perf_counter() - start_time
                logger.info(
                    "LLM provider=%s latency=%.3fs attempts=%s",
                    provider,
                    latency,
                    attempt,
                )
                return LLMResult(text=text, provider=provider, latency=latency, attempts=attempt)
            except Exception as exc:
                last_error = exc
                if attempt <= config.LLM_RETRIES:
                    await asyncio.sleep(0.1 * attempt)

        raise LLMProviderError(str(last_error))

    async def _openrouter(self, prompt: str) -> str:
        if not config.OPENROUTER_API_KEY:
            raise LLMProviderError("OPENROUTER_API_KEY is not set")

        payload = {
            "model": config.OPENROUTER_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": config.LLM_MAX_TOKENS,
        }
        headers = {
            "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/Hassan-Hazem/Disturbed-Computing-",
            "X-Title": "Distributed LLM Load Balancer",
        }
        data = await asyncio.wait_for(
            asyncio.to_thread(
                _post_json,
                "https://openrouter.ai/api/v1/chat/completions",
                payload,
                headers,
                config.LLM_TIMEOUT,
            ),
            timeout=config.LLM_TIMEOUT + 1,
        )
        return data["choices"][0]["message"]["content"].strip()

    async def _huggingface(self, prompt: str) -> str:
        if not config.HUGGINGFACE_API_KEY:
            raise LLMProviderError("HUGGINGFACE_API_KEY is not set")

        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": config.LLM_MAX_TOKENS,
                "return_full_text": False,
            },
        }
        headers = {
            "Authorization": f"Bearer {config.HUGGINGFACE_API_KEY}",
            "Content-Type": "application/json",
        }
        url = f"https://api-inference.huggingface.co/models/{config.HUGGINGFACE_MODEL}"
        data = await asyncio.wait_for(
            asyncio.to_thread(_post_json, url, payload, headers, config.LLM_TIMEOUT),
            timeout=config.LLM_TIMEOUT + 1,
        )

        if isinstance(data, list) and data:
            return data[0].get("generated_text", "").strip()
        if isinstance(data, dict):
            return data.get("generated_text") or data.get("summary_text") or json.dumps(data)
        raise LLMProviderError("unexpected HuggingFace response format")

    async def _ollama(self, prompt: str) -> str:
        payload = {
            "model": config.OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": config.LLM_MAX_TOKENS},
        }
        headers = {"Content-Type": "application/json"}
        url = f"{config.OLLAMA_BASE_URL.rstrip('/')}/api/generate"
        data = await asyncio.wait_for(
            asyncio.to_thread(_post_json, url, payload, headers, config.LLM_TIMEOUT),
            timeout=config.LLM_TIMEOUT + 1,
        )
        return data.get("response", "").strip()

    async def _simulated(self, query: str, context: str) -> str:
        base_latency = config.LLM_BASE_LATENCY
        query_complexity = len(query.split()) * config.QUERY_COMPLEXITY_FACTOR
        random_variance = random.uniform(0.0, config.LLM_VARIANCE)
        await asyncio.sleep(base_latency + query_complexity + random_variance)
        return (
            "[SIMULATED LLM] "
            f"Answer to '{query}' grounded in retrieved context: {context[:300]}"
        )


_default_client = LLMClient()


async def run_llm_async(query: str, context: str) -> LLMResult:
    return await _default_client.complete(query, context)


def run_llm(query: str, context: str) -> str:
    """Synchronous compatibility wrapper for older call sites."""
    return asyncio.run(run_llm_async(query, context)).text
