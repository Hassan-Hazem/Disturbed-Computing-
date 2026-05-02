# Distributed LLM System: Load Balancing and Fault Tolerance

This repository implements a distributed LLM serving simulation that builds on the original project structure:

- `client/` generates concurrent requests.
- `lb/` routes requests across workers.
- `master/` tracks scheduling state and worker status.
- `workers/` execute RAG plus LLM inference.
- `rag/` retrieves top-k context using embeddings.
- `llm/` wraps real LLM providers with retries and timeout handling.
- `common/` contains shared models and metrics.

The system is designed to demonstrate efficient load balancing and GPU-cluster task distribution for 1000+ concurrent LLM requests.

## What Is Implemented

- Async concurrency with `asyncio` tasks instead of one OS thread per user.
- Round robin, least connections, and load-aware routing.
- Worker capacity limits through async semaphores.
- Worker health state, failure injection, recovery, and task reassignment.
- Real LLM API wrapper for OpenRouter, HuggingFace Inference API, and Ollama.
- Simulated LLM fallback for offline load testing, clearly labeled as `simulated`.
- RAG retrieval with normalized hashed embeddings and top-k cosine search.
- Optional FAISS acceleration when `faiss` and `numpy` are installed.
- Latency, throughput, reassignment, provider, and per-worker utilization metrics.
- File logging to `distributed_llm.log`.

## How to Run

From the repository root:

```powershell
python main.py
```

Run a 1000-user fault-tolerance test:

```powershell
python main.py --users 1000 --workers 4 --strategy load_aware --failures on
```

Compare load-balancing strategies:

```powershell
python test_strategies.py
```

Run a smaller smoke test:

```powershell
python test_quick.py
```

## Real LLM Providers

The code uses real provider integrations when credentials or local provider settings are configured.

OpenRouter:

```powershell
$env:LLM_PROVIDER="openrouter"
$env:OPENROUTER_API_KEY="your_key"
$env:OPENROUTER_MODEL="meta-llama/llama-3.1-8b-instruct:free"
python main.py --users 20 --failures off
```

HuggingFace:

```powershell
$env:LLM_PROVIDER="huggingface"
$env:HUGGINGFACE_API_KEY="your_key"
$env:HUGGINGFACE_MODEL="mistralai/Mistral-7B-Instruct-v0.3"
python main.py --users 20 --failures off
```

Ollama:

```powershell
$env:LLM_PROVIDER="ollama"
$env:OLLAMA_BASE_URL="http://localhost:11434"
$env:OLLAMA_MODEL="llama3.1"
python main.py --users 20 --failures off
```

To require real AI and disable the offline simulator:

```powershell
$env:ALLOW_SIMULATED_LLM="false"
python main.py --users 20 --failures off
```

## Configuration

Most settings can be changed in `config.py` or with environment variables:

- `NUM_WORKERS`: number of worker nodes.
- `NUM_USERS`: number of client requests.
- `LOAD_BALANCING_STRATEGY`: `round_robin`, `least_connections`, or `load_aware`.
- `WORKER_PARALLELISM`: concurrent tasks per worker.
- `CLIENT_CONCURRENCY_LIMIT`: max active client tasks.
- `SIMULATE_FAILURES`: enable worker failure simulation.
- `FAILURE_TRIGGER_TIME`: seconds before killing a worker.
- `FAILURE_RECOVERY_TIME`: seconds before recovery.
- `WORKERS_TO_FAIL`: number of workers to fail.
- `LLM_PROVIDER`: `auto`, `openrouter`, `huggingface`, `ollama`, or `simulated`.
- `LLM_TIMEOUT`, `LLM_RETRIES`, `LLM_MAX_TOKENS`: provider call behavior.
- `RAG_TOP_K`: number of retrieved documents injected into the prompt.

## Architecture

```text
Client load generator
        |
        v
Master scheduler
        |
        v
Load balancer
  | round_robin
  | least_connections
  | load_aware
        |
        v
GPU worker pool
  | async capacity limit
  | RAG retrieval
  | real LLM provider wrapper
        |
        v
Response + metrics
```

## Testing Failure Reassignment

The failure simulation marks one worker inactive while requests are in flight. Requests that were assigned to that worker raise a failure, return to the load balancer, and are reassigned to another active worker. The scheduler records reassignment counts so the final metrics show no request loss when healthy workers remain.

Example command:

```powershell
$env:FAILURE_TRIGGER_TIME="0.05"
$env:FAILURE_RECOVERY_TIME="2.0"
$env:WORKERS_TO_FAIL="1"
python main.py --users 1000 --failures on
```

## Verified Local Results

Local run on May 2, 2026:

- Command: `python main.py --users 1000 --failures on`
- Workers: 4
- Worker parallelism: 8
- Strategy: `load_aware`
- Successful requests: 1000 / 1000
- Failed final requests: 0
- Reassigned requests: 250
- Average latency: about 0.428 s
- P95 latency: about 0.521 s
- Throughput: about 55 successful requests/sec

The local run used the offline simulated provider because no OpenRouter, HuggingFace, or Ollama credentials were configured in this environment. The real provider wrapper is implemented in `llm/inference.py`.
