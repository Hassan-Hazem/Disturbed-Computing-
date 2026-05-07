# Quick Start

The final delivery path uses a real LLM only. The default provider is an
OpenAI-compatible server, intended for Thunder Compute running vLLM.

## 1. Configure Thunder/vLLM Provider

If using Thunder's forwarded port URL:

```powershell
$env:LLM_PROVIDER="openai_compatible"
$env:OPENAI_COMPATIBLE_BASE_URL="https://INSTANCE_UUID-8000.thundercompute.net/v1"
$env:OPENAI_COMPATIBLE_MODEL="Qwen/Qwen2.5-1.5B-Instruct"
$env:OPENAI_COMPATIBLE_API_KEY="EMPTY"
```

If using SSH tunnel:

```powershell
$env:LLM_PROVIDER="openai_compatible"
$env:OPENAI_COMPATIBLE_BASE_URL="http://localhost:8000/v1"
$env:OPENAI_COMPATIBLE_MODEL="Qwen/Qwen2.5-1.5B-Instruct"
$env:OPENAI_COMPATIBLE_API_KEY="EMPTY"
```

## 2. Configure Load-Test Settings

```powershell
$env:CLIENT_CONCURRENCY_LIMIT="128"
$env:HTTP_CLIENT_THREADS="128"
$env:WORKER_PARALLELISM="32"
$env:LLM_TIMEOUT="300"
$env:LLM_RETRIES="2"
$env:LLM_MAX_TOKENS="64"
```

## 3. Provider Smoke Test

```powershell
python test_real_llm_provider.py
```

Expected:

```text
Provider: openai_compatible
Latency: ...
Response:
...
```

## 4. Small Real Test

```powershell
python main.py --users 20 --workers 4 --strategy round_robin --failures off
```

## 5. Fault-Tolerance Test

```powershell
$env:FAILURE_TRIGGER_TIME="1"
$env:FAILURE_RECOVERY_TIME="10"
$env:MAX_TASK_RETRIES="8"
$env:REASSIGNMENT_BACKOFF="0.5"

python main.py --users 50 --workers 4 --strategy round_robin --failures on
```

## 6. Final 1000-Request Real LLM Test

```powershell
python main.py --users 1000 --workers 8 --strategy round_robin --failures off
```

Then:

```powershell
python main.py --users 1000 --workers 8 --strategy round_robin --failures on
```

For full Thunder setup details, read `THUNDER_COMPUTE_RUNBOOK.md`.
