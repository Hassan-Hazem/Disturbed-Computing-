# Efficient Load Balancing and GPU Cluster Task Distribution for 1000+ Real LLM Requests

## Introduction

This project implements a distributed LLM serving system. The goal is to accept
many concurrent user requests, distribute them across logical workers, retrieve
relevant context using RAG, send prompts to a real GPU-hosted LLM, and report
performance metrics.

## Problem Definition

Serving LLM requests is expensive because inference is limited by GPU capacity.
If many users send requests at once, the system needs scheduling, load
balancing, fault handling, and observability. The project demonstrates these
distributed systems concepts using a real Thunder Compute GPU node running an
OpenAI-compatible LLM server.

## System Architecture

The system has five main layers:

- Client load generator: creates concurrent requests.
- Master scheduler: tracks in-flight, completed, failed, and reassigned tasks.
- Load balancer: assigns tasks to workers, mainly using round robin.
- Worker nodes: retrieve RAG context and call the real LLM API.
- Monitoring: reports latency, throughput, success rate, and worker usage.

## Implementation Details

The project uses Python `asyncio` to generate high concurrency. Workers use
capacity controls so many logical workers can call the external GPU inference
server without blocking the whole application. The real LLM layer supports two
providers only: `openai_compatible` for Thunder/vLLM and `ollama` for local
fallback testing.

## Load Balancing Strategy

The primary strategy for delivery is round robin. Requests are assigned in order:

```text
Worker 1, Worker 2, Worker 3, Worker 4, then Worker 1 again
```

This gives a fair distribution and is simple to explain. The code also contains
least-connections and load-aware strategies for comparison, but round robin is
the main project demo.

## LLM Integration

The final LLM integration uses Thunder Compute running vLLM. vLLM exposes an
OpenAI-compatible endpoint:

```text
http://THUNDER_IP:8000/v1/chat/completions
```

The project sends RAG-enhanced prompts to this endpoint and records provider
latency per request.

Recommended model:

```text
Qwen/Qwen2.5-1.5B-Instruct
```

## RAG Pipeline

The RAG module stores a small distributed-systems knowledge dataset. For each
request, it embeds the user query, scores documents by cosine similarity, selects
the top-k documents, and injects those documents into the LLM prompt.

## Fault Tolerance

Fault tolerance means the system continues operating when a worker fails. During
the failure demo, one worker is marked inactive. The load balancer skips inactive
workers, and failed in-flight requests are retried on another active worker.
The worker later recovers and rejoins the cluster.

## Testing and Results

Required tests:

```powershell
python test_real_llm_provider.py
python main.py --users 20 --workers 4 --strategy round_robin --failures off
python main.py --users 1000 --workers 8 --strategy round_robin --failures off
python main.py --users 1000 --workers 8 --strategy round_robin --failures on
```

Success criteria:

- Provider is `openai_compatible`.
- 1000 total requests are generated.
- Success rate is at least 95%.
- Metrics show average latency, p95 latency, throughput, and per-worker counts.
- Failure test shows failure detection, reassignment, and recovery.

## Limitations

The workers are logical Python workers rather than separate physical machines.
The real inference bottleneck is the Thunder GPU node. Throughput depends on the
GPU type, model size, max tokens, and vLLM settings.

## Future Work

Future improvements include physical worker processes, gRPC communication,
persistent queues, dynamic autoscaling, live dashboards, and multi-GPU serving.
