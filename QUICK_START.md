# Quick Start

## Smoke Test

```powershell
python test_quick.py
```

This runs 100 async users, uses `load_aware` routing, kills one worker during execution, and verifies reassignment.

## 1000-User Test

```powershell
python main.py --users 1000 --workers 4 --strategy load_aware --failures on
```

## Strategy Comparison

```powershell
python test_strategies.py
```

## Real LLM Mode

OpenRouter:

```powershell
$env:LLM_PROVIDER="openrouter"
$env:OPENROUTER_API_KEY="your_key"
python main.py --users 20 --failures off
```

HuggingFace:

```powershell
$env:LLM_PROVIDER="huggingface"
$env:HUGGINGFACE_API_KEY="your_key"
python main.py --users 20 --failures off
```

Ollama:

```powershell
$env:LLM_PROVIDER="ollama"
$env:OLLAMA_MODEL="llama3.1"
python main.py --users 20 --failures off
```

Disable offline simulation:

```powershell
$env:ALLOW_SIMULATED_LLM="false"
python main.py --users 20 --failures off
```

## Useful Configuration

```powershell
$env:NUM_WORKERS="8"
$env:WORKER_PARALLELISM="16"
$env:CLIENT_CONCURRENCY_LIMIT="1000"
$env:LOAD_BALANCING_STRATEGY="least_connections"
python main.py
```

Logs are written to `distributed_llm.log`.
