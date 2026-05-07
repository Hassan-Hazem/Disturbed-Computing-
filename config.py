import os

# Configuration file for Distributed LLM System.
# Values can be overridden through environment variables for experiments.

# System Configuration
NUM_WORKERS = int(os.getenv("NUM_WORKERS", "4"))
NUM_USERS = int(os.getenv("NUM_USERS", "1000"))
LOAD_BALANCING_STRATEGY = os.getenv("LOAD_BALANCING_STRATEGY", "round_robin")
WORKER_PARALLELISM = int(os.getenv("WORKER_PARALLELISM", "16"))
CLIENT_CONCURRENCY_LIMIT = int(os.getenv("CLIENT_CONCURRENCY_LIMIT", "1000"))
HTTP_CLIENT_THREADS = int(os.getenv("HTTP_CLIENT_THREADS", "128"))

# Failure Simulation
SIMULATE_FAILURES = os.getenv("SIMULATE_FAILURES", "true").lower() == "true"
FAILURE_TRIGGER_TIME = float(os.getenv("FAILURE_TRIGGER_TIME", "0.05"))
FAILURE_RECOVERY_TIME = float(os.getenv("FAILURE_RECOVERY_TIME", "2.0"))
WORKERS_TO_FAIL = int(os.getenv("WORKERS_TO_FAIL", "1"))
MAX_TASK_RETRIES = int(os.getenv("MAX_TASK_RETRIES", "3"))
REASSIGNMENT_BACKOFF = float(os.getenv("REASSIGNMENT_BACKOFF", "0.02"))

# Performance Settings
ROUTING_DEFAULT_LATENCY = float(os.getenv("ROUTING_DEFAULT_LATENCY", "1.0"))
WORKER_LOCAL_OVERHEAD = float(os.getenv("WORKER_LOCAL_OVERHEAD", "0.0"))

# Real LLM provider configuration.
# LLM_PROVIDER: openai_compatible for Thunder/vLLM, or ollama for local fallback.
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai_compatible").lower()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
OPENAI_COMPATIBLE_BASE_URL = os.getenv("OPENAI_COMPATIBLE_BASE_URL", "http://localhost:8000/v1")
OPENAI_COMPATIBLE_API_KEY = os.getenv("OPENAI_COMPATIBLE_API_KEY", "EMPTY")
OPENAI_COMPATIBLE_MODEL = os.getenv("OPENAI_COMPATIBLE_MODEL", "Qwen/Qwen2.5-1.5B-Instruct")
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "300"))
LLM_RETRIES = int(os.getenv("LLM_RETRIES", "2"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "64"))

# RAG Configuration
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "3"))
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "384"))

# Monitoring
ENABLE_DETAILED_LOGGING = os.getenv("ENABLE_DETAILED_LOGGING", "false").lower() == "true"
COLLECT_PERFORMANCE_METRICS = os.getenv("COLLECT_PERFORMANCE_METRICS", "true").lower() == "true"
PRINT_METRICS_INTERVAL = int(os.getenv("PRINT_METRICS_INTERVAL", "100"))
LOG_FILE = os.getenv("LOG_FILE", "distributed_llm.log")
