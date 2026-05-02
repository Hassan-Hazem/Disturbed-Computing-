# Efficient Load Balancing and GPU Cluster Task Distribution for 1000+ Concurrent LLM Requests

## Introduction

Large language model applications receive bursts of concurrent requests that must be routed across limited GPU resources. This project implements a distributed serving prototype that combines load balancing, worker health tracking, retrieval augmented generation, real LLM API wrappers, and fault-tolerant reassignment. The implementation evolves the existing repository structure instead of replacing it.

## Problem Definition

The target problem is to serve 1000+ concurrent LLM requests with low request loss and observable performance. The system must distribute work across multiple GPU-like workers, avoid overloaded nodes, detect worker failure, reassign failed tasks, retrieve relevant context for each query, and support real AI providers such as OpenRouter, HuggingFace, and Ollama.

## System Architecture

The repository is organized into layers:

- `client/load_generator.py`: creates asynchronous client requests.
- `master/scheduler.py`: tracks in-flight, completed, failed, and reassigned requests.
- `lb/load_balancer.py`: chooses workers using round robin, least connections, or load-aware routing.
- `workers/gpu_worker.py`: represents GPU workers with capacity limits, failure state, RAG, and LLM inference.
- `rag/retriever.py`: embeds documents and retrieves top-k relevant context.
- `llm/inference.py`: calls real LLM providers with retries, timeouts, and latency logging.
- `common/monitoring.py`: aggregates latency, throughput, provider, and worker metrics.

## Implementation Details

The client was upgraded from thread-per-user execution to `asyncio`, allowing the project to schedule 1000 users without creating 1000 OS threads. Each worker uses an async semaphore to model GPU parallelism. The scheduler records task state, the load balancer performs bounded retries, and the worker returns the real `worker_id` that completed each request.

The `config.py` module now supports environment-variable overrides for workers, concurrency, provider selection, retries, failure timing, and RAG top-k. The `main.py` entry point accepts command-line options for users, workers, strategy, and failure simulation.

## Load Balancing Strategies

Round robin distributes requests cyclically across active workers. It is simple and fair for homogeneous worker capacity.

Least connections chooses the active worker with the fewest current requests. This adapts better when request execution times differ.

Load-aware routing evaluates worker utilization, active connections, historical average latency, failure count, and worker id. This makes the balancer prefer healthy, less busy, lower-latency workers.

## LLM Integration

`llm/inference.py` implements provider wrappers for:

- OpenRouter chat completions.
- HuggingFace Inference API.
- Local Ollama generation.

Each call uses a prompt that includes retrieved RAG context. The wrapper applies timeout handling, retry logic, provider fallback in `auto` mode, and request latency logging. If no real provider is configured, the system can run an explicitly labeled `simulated` provider for offline load testing. Setting `ALLOW_SIMULATED_LLM=false` enforces real-provider execution.

## RAG Pipeline

The RAG module includes a sample distributed-systems dataset. It embeds each document using normalized hashed vectors, embeds the query, performs top-k cosine retrieval, and injects the selected context into the LLM prompt. FAISS is used automatically when available; otherwise the standard-library cosine index keeps the project runnable without external packages.

## Fault Tolerance

Worker failure is simulated by marking a worker inactive during active load. The load balancer stops routing new work to inactive workers. If a worker fails during processing, the request raises an exception, is counted as a reassignment, and is retried on another active worker. Recovery reactivates the worker after a configurable delay.

## Testing and Results

Commands used:

```powershell
python test_quick.py
python test_strategies.py
python main.py --users 1000 --failures on
```

Observed local 1000-user result on May 2, 2026:

- Successful requests: 1000 / 1000.
- Final failed requests: 0.
- Reassigned requests: 250.
- Average latency: about 0.428 seconds.
- P95 latency: about 0.521 seconds.
- Throughput: about 55 successful requests per second.
- Failed worker recovered and rejoined the cluster.

The local result used the simulated provider because no API credentials or local Ollama server were configured. Real provider execution is supported through environment variables.

## Limitations

The current system runs as a single Python process, so workers are simulated nodes rather than separate machines. GPU behavior is represented with capacity limits and delay instead of CUDA execution. The default embedding implementation is a lightweight hashing approach; FAISS acceleration is optional. Real LLM throughput depends on external provider rate limits, API latency, and model availability.

## Future Work

Future improvements include adding gRPC between master and workers, true multi-process or multi-host workers, persistent queues for crash recovery, adaptive autoscaling, batching for GPU efficiency, circuit breakers for provider failures, a dashboard for live metrics, and a production vector database such as ChromaDB or a required FAISS dependency.
