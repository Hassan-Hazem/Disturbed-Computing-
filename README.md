# Distributed LLM System — CSE354

A distributed LLM inference system with pluggable load balancing, fault tolerance, RAG integration, and real-time performance monitoring. Built for Ain Shams University CSE354.

---

## Features

- **Three load balancing strategies** — Round Robin, Least Connections, Load-Aware
- **Fault tolerance** — automatic worker failure detection and in-flight task reassignment with exponential backoff
- **RAG pipeline** — hash-based (Blake2b) vector embeddings, cosine similarity search, optional FAISS acceleration
- **Async concurrency** — `asyncio`-native pipeline; each worker holds a semaphore of configurable capacity
- **Real LLM inference** — OpenAI-compatible endpoint (Thunder Compute + vLLM) or local Ollama fallback
- **Performance monitoring** — avg/min/max/P95 latency, throughput, per-worker stats

---

## Repository Structure

```
.
├── main.py                  # Entry point
├── config.py                # All tuneable parameters (env-var overrideable)
├── client/
│   └── load_generator.py    # Async load test driver
├── common/
│   ├── models.py            # Request / Response dataclasses
│   └── monitoring.py        # PerformanceMonitor (thread-safe metrics)
├── lb/
│   └── load_balancer.py     # LoadBalancer — strategy dispatch & retry logic
├── master/
│   └── scheduler.py         # Scheduler — orchestrates workers and monitors
├── workers/
│   └── gpu_worker.py        # GPUWorker — semaphore-gated async processing
├── llm/
│   └── inference.py         # LLMClient — openai_compatible / ollama providers
└── rag/
    └── retriever.py         # VectorRetriever — embed → search → context string
```

---

## Quickstart

### 1. Install dependencies

```bash
pip install httpx  # only stdlib + optional faiss/numpy needed otherwise
```

For FAISS acceleration (optional):

```bash
pip install faiss-cpu numpy
```

### 2. Configure the LLM backend

**Thunder Compute / vLLM (recommended):**

```bash
export LLM_PROVIDER=openai_compatible
export OPENAI_COMPATIBLE_BASE_URL=http://<your-thunder-host>:8000/v1
export OPENAI_COMPATIBLE_MODEL=Qwen/Qwen2.5-1.5B-Instruct
export OPENAI_COMPATIBLE_API_KEY=EMPTY
```

**Local Ollama fallback:**

```bash
export LLM_PROVIDER=ollama
export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_MODEL=llama3.2:3b
```

### 3. Run

```bash
# Default: 4 workers, 1000 users, round_robin, failures ON
python main.py

# Custom flags
python main.py --workers 4 --users 50 --strategy load_aware --failures off
```

---

## Configuration Reference

All values in `config.py` can be overridden with environment variables.

| Variable | Default | Description |
|---|---|---|
| `NUM_WORKERS` | `4` | Number of GPU worker nodes |
| `NUM_USERS` | `1000` | Concurrent simulated users |
| `LOAD_BALANCING_STRATEGY` | `round_robin` | `round_robin` / `least_connections` / `load_aware` |
| `WORKER_PARALLELISM` | `16` | Semaphore slots per worker |
| `CLIENT_CONCURRENCY_LIMIT` | `1000` | Max concurrent client coroutines |
| `SIMULATE_FAILURES` | `true` | Toggle worker failure simulation |
| `FAILURE_TRIGGER_TIME` | `0.05` | Fraction of test elapsed before failure fires |
| `FAILURE_RECOVERY_TIME` | `2.0` | Seconds until a failed worker recovers |
| `WORKERS_TO_FAIL` | `1` | How many workers to fail simultaneously |
| `MAX_TASK_RETRIES` | `3` | Max reassignment attempts per request |
| `REASSIGNMENT_BACKOFF` | `0.02` | Seconds to wait between reassignments |
| `LLM_PROVIDER` | `openai_compatible` | `openai_compatible` or `ollama` |
| `LLM_TIMEOUT` | `300` | Per-request timeout (seconds) |
| `LLM_RETRIES` | `2` | LLM-level retry attempts |
| `LLM_MAX_TOKENS` | `64` | Max tokens per LLM response |
| `RAG_TOP_K` | `3` | Documents retrieved per query |
| `EMBEDDING_DIMENSIONS` | `384` | Hash embedding vector size |

---

## Load Balancing Strategies

### Round Robin
Cycles through workers in order. Simple and fair for homogeneous workloads.

### Least Connections
Routes each request to the worker with the fewest active connections. Better for uneven request durations.

### Load-Aware
Ranks workers by a composite score: utilization → active connections → average latency → failure count. Avoids overloaded and unhealthy workers.

---

## Fault Tolerance

When `SIMULATE_FAILURES=true`, one worker is marked inactive after `FAILURE_TRIGGER_TIME × test_duration` seconds and recovers after `FAILURE_RECOVERY_TIME` seconds. The load balancer excludes failed workers from the candidate set. In-flight requests that hit a failed worker are retried on another worker after `REASSIGNMENT_BACKOFF` seconds, up to `MAX_TASK_RETRIES` attempts.

---

## RAG Pipeline

1. Each document in `SAMPLE_DATASET` is embedded at startup using `embed_text()` — a Blake2b token-hashing approach that produces normalized float vectors.
2. On each request, the query is embedded and compared against all document embeddings via cosine similarity (or FAISS `IndexFlatIP` if installed).
3. The top-k documents are formatted into a context string and injected into the LLM prompt.

---

## Testing

```bash
# Quick smoke test (no real LLM required)
python test_quick.py

# Strategy comparison
python test_strategies.py

# Real LLM provider round-trip
python test_real_llm_provider.py
```

---

## Infrastructure (Demo Setup)

- **GPU**: NVIDIA RTX A6000 (49 GB VRAM) via [Thunder Compute](https://thundercompute.com)
- **LLM server**: vLLM serving `Qwen/Qwen2.5-1.5B-Instruct` with prefix caching enabled (96.2% cache hit rate observed)
- **Endpoint**: OpenAI-compatible `/v1/chat/completions`

---

## Authors

CSE354 — Distributed Computing, Ain Shams University
