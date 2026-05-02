import os

# Configuration file for Distributed LLM System.
# Values can be overridden through environment variables for experiments.

# System Configuration
NUM_WORKERS = int(os.getenv("NUM_WORKERS", "4"))
NUM_USERS = int(os.getenv("NUM_USERS", "1000"))
LOAD_BALANCING_STRATEGY = os.getenv("LOAD_BALANCING_STRATEGY", "load_aware")
WORKER_PARALLELISM = int(os.getenv("WORKER_PARALLELISM", "8"))
CLIENT_CONCURRENCY_LIMIT = int(os.getenv("CLIENT_CONCURRENCY_LIMIT", "1000"))

# Failure Simulation
SIMULATE_FAILURES = os.getenv("SIMULATE_FAILURES", "true").lower() == "true"
FAILURE_TRIGGER_TIME = float(os.getenv("FAILURE_TRIGGER_TIME", "0.05"))
FAILURE_RECOVERY_TIME = float(os.getenv("FAILURE_RECOVERY_TIME", "2.0"))
WORKERS_TO_FAIL = int(os.getenv("WORKERS_TO_FAIL", "1"))
MAX_TASK_RETRIES = int(os.getenv("MAX_TASK_RETRIES", "3"))
REASSIGNMENT_BACKOFF = float(os.getenv("REASSIGNMENT_BACKOFF", "0.02"))

# Performance Settings
LLM_BASE_LATENCY = float(os.getenv("LLM_BASE_LATENCY", "0.15"))
LLM_VARIANCE = float(os.getenv("LLM_VARIANCE", "0.1"))
QUERY_COMPLEXITY_FACTOR = float(os.getenv("QUERY_COMPLEXITY_FACTOR", "0.02"))
GPU_SIMULATION_DELAY = float(os.getenv("GPU_SIMULATION_DELAY", "0.015"))

# Real LLM provider configuration.
# LLM_PROVIDER: auto, openrouter, huggingface, ollama, simulated.
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "auto").lower()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")
HUGGINGFACE_MODEL = os.getenv("HUGGINGFACE_MODEL", "mistralai/Mistral-7B-Instruct-v0.3")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "20"))
LLM_RETRIES = int(os.getenv("LLM_RETRIES", "2"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "160"))
ALLOW_SIMULATED_LLM = os.getenv("ALLOW_SIMULATED_LLM", "true").lower() == "true"

# RAG Configuration
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "3"))
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "384"))

# Monitoring
ENABLE_DETAILED_LOGGING = os.getenv("ENABLE_DETAILED_LOGGING", "false").lower() == "true"
COLLECT_PERFORMANCE_METRICS = os.getenv("COLLECT_PERFORMANCE_METRICS", "true").lower() == "true"
PRINT_METRICS_INTERVAL = int(os.getenv("PRINT_METRICS_INTERVAL", "100"))
LOG_FILE = os.getenv("LOG_FILE", "distributed_llm.log")
