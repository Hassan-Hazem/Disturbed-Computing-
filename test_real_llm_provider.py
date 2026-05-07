"""
Smoke test for real LLM provider connectivity.

Use this before a full load test. It only accepts real providers:
Thunder/vLLM through OpenAI-compatible API, or Ollama.
"""

import asyncio
import sys

from llm.inference import run_llm_async


async def main() -> int:
    result = await run_llm_async(
        query="In one sentence, explain least-connections load balancing.",
        context=(
            "Least-connections load balancing routes a new request to the "
            "healthy worker with the fewest active requests."
        ),
    )

    print(f"Provider: {result.provider}")
    print(f"Latency: {result.latency:.3f}s")
    print(f"Attempts: {result.attempts}")
    print("Response:")
    print(result.text.strip())

    if not result.text.strip():
        print("\nERROR: provider returned an empty response.", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
