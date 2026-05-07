# Distributed LLM Load Balancing System

This project serves many LLM requests through a distributed architecture:

```text
Client load generator
        |
        v
Master scheduler
        |
        v
Round-robin load balancer
        |
        v
Logical GPU workers
        |
        v
RAG retrieval + real LLM API call
        |
        v
Metrics and response
```

The final delivery uses a real GPU inference server on Thunder Compute. The
project calls that server through an OpenAI-compatible API, usually vLLM.

## Main Features

- Real LLM calls only: Thunder/vLLM or Ollama.
- Round-robin load balancing for the main demo.
- Optional least-connections and load-aware strategies for comparison.
- Async client load generation for 1000 total requests.
- Worker failure simulation, retry, and reassignment.
- RAG top-k context retrieval.
- Metrics for latency, throughput, success rate, reassignment, provider, and worker distribution.

## Providers

The code intentionally keeps only the providers we use:

- `openai_compatible`: Thunder Compute running vLLM.
- `ollama`: local fallback, such as Hassan's laptop.

No OpenRouter, HuggingFace, LM Studio, or simulation provider remains in the
runtime path.

## Recommended Final Provider

Use Thunder Compute with vLLM:

```text
Qwen/Qwen2.5-1.5B-Instruct
```

This model is small, fast, and suitable for a 1000-request real load test.

## Quick Run

Configure Zayed laptop to call Thunder/vLLM through Thunder's forwarded port URL:

```powershell
$env:LLM_PROVIDER="openai_compatible"
$env:OPENAI_COMPATIBLE_BASE_URL="https://INSTANCE_UUID-8000.thundercompute.net/v1"
$env:OPENAI_COMPATIBLE_MODEL="Qwen/Qwen2.5-1.5B-Instruct"
$env:OPENAI_COMPATIBLE_API_KEY="EMPTY"
$env:CLIENT_CONCURRENCY_LIMIT="128"
$env:HTTP_CLIENT_THREADS="128"
$env:WORKER_PARALLELISM="32"
$env:LLM_TIMEOUT="300"
$env:LLM_MAX_TOKENS="64"
```

Smoke test:

```powershell
python test_real_llm_provider.py
```

Small system test:

```powershell
python main.py --users 20 --workers 4 --strategy round_robin --failures off
```

Final real load:

```powershell
python main.py --users 1000 --workers 8 --strategy round_robin --failures off
```

Fault-tolerance run:

```powershell
python main.py --users 1000 --workers 8 --strategy round_robin --failures on
```

See `THUNDER_COMPUTE_RUNBOOK.md` for the full cloud setup.

## How It Works

`main.py` reads command-line arguments, creates workers, creates the load
balancer, creates the scheduler, starts the client load generator, and prints
metrics.

The client creates many concurrent requests. The scheduler marks each request as
in-flight. The load balancer assigns each request to a worker. The worker
retrieves RAG context and calls the configured real LLM provider. The monitor
records success/failure, latency, provider, and worker usage.

## Important Delivery Note

The 1000-request run is real when `Provider: openai_compatible` appears in the
metrics. The requests are all answered by the Thunder GPU model server, not by a
simulator.
