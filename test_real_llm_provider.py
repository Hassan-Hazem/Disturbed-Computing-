"""
Smoke test for real LLM provider connectivity.

Use this before a full load test. By default it fails if the provider falls
back to the simulator, because the goal is to prove real LLM inference works.
"""

import argparse
import asyncio
import sys

from llm.inference import run_llm_async


async def main() -> int:
    parser = argparse.ArgumentParser(description="Test configured LLM provider")
    parser.add_argument(
        "--allow-simulated",
        action="store_true",
        help="Allow the simulated fallback to count as success",
    )
    args = parser.parse_args()

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

    if result.provider == "simulated" and not args.allow_simulated:
        print("\nERROR: provider fell back to simulated mode.", file=sys.stderr)
        print("Set a real provider env var or pass --allow-simulated.", file=sys.stderr)
        return 1

    if not result.text.strip():
        print("\nERROR: provider returned an empty response.", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
