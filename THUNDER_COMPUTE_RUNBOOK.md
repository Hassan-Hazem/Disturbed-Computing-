# Thunder Compute Real LLM Runbook

This project now targets a real GPU inference server for the 1000-user run.
Use Thunder Compute to host the model, then run the distributed client project
from Zayed's laptop.

## Why Thunder Compute + vLLM

Ollama on Hassan's RTX 2070 proved the real LLM path works, but one laptop
cannot handle 1000 real requests quickly. Thunder Compute gives us a stronger
GPU. vLLM exposes an OpenAI-compatible API, which is ideal for high-throughput
serving and already matches the project's `openai_compatible` provider.

Recommended first model:

```text
Qwen/Qwen2.5-1.5B-Instruct
```

Why this model:

- It is small enough to run fast.
- It is not gated.
- It is good enough for short RAG answers.
- It keeps the $20 credit safer than a large 7B/14B model.

After the 1.5B model works, you can try:

```text
Qwen/Qwen2.5-7B-Instruct
```

only if the selected GPU has enough VRAM and the budget allows it.

## Step 1: Create Thunder Compute GPU Node

In Thunder Compute console:

1. Create a GPU instance.
2. Choose Ubuntu.
3. Choose a CUDA/PyTorch image if available.
4. Prefer a GPU with at least 16 GB VRAM for the first demo.
5. Add your SSH key or use the console terminal.
6. Start the instance.
7. Copy the public IP address.

Call it:

```text
THUNDER_IP
```

## Step 2: SSH Into The Node

Easiest path: use the Thunder console terminal or the Thunder CLI/VS Code
connect button.

If you use manual SSH, Thunder may not use port 22. Copy the exact `IP:Port`
from the instance details, then connect like this:

```powershell
ssh -p SSH_PORT ubuntu@THUNDER_IP
```

If the username is different in the Thunder console, use that username instead.

## Step 3: Install vLLM

On the Thunder node:

```bash
python3 --version
nvidia-smi
python3 -m pip install --upgrade pip
python3 -m pip install vllm
```

`nvidia-smi` must show the GPU. If it does not, stop and fix the instance image.

## Step 4: Start The Real LLM Server

On the Thunder node:

```bash
vllm serve Qwen/Qwen2.5-1.5B-Instruct \
  --host 0.0.0.0 \
  --port 8000 \
  --max-model-len 2048 \
  --max-num-seqs 128
```

Keep this terminal open. This command starts an OpenAI-compatible LLM API at:

```text
http://THUNDER_IP:8000/v1
```

## Step 5: Expose Port 8000

Option A, Thunder Console port forwarding:

1. Select the running instance.
2. Click `Forward Ports`.
3. Enter `8000`.
4. Thunder gives you an HTTPS URL like:

```text
https://INSTANCE_UUID-8000.thundercompute.net
```

Use this as the project base URL with `/v1` added:

```text
https://INSTANCE_UUID-8000.thundercompute.net/v1
```

Option B, local SSH tunnel:

```powershell
ssh -L 8000:localhost:8000 -p SSH_PORT ubuntu@THUNDER_IP
```

Keep that PowerShell window open.

Then your local API URL is:

```text
http://localhost:8000/v1
```

## Step 6: Configure The Project On Zayed Laptop

From the project folder:

```powershell
cd "C:\Users\abdra\OneDrive\Documents\GitHub\Disturbed-Computing-"
```

If using Thunder forwarded HTTPS URL:

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

Use these stable load settings first:

```powershell
$env:CLIENT_CONCURRENCY_LIMIT="128"
$env:HTTP_CLIENT_THREADS="128"
$env:WORKER_PARALLELISM="32"
$env:LLM_TIMEOUT="300"
$env:LLM_RETRIES="2"
$env:LLM_MAX_TOKENS="64"
```

## Step 7: Provider Smoke Test

On Zayed laptop:

```powershell
python test_real_llm_provider.py
```

Success criteria:

- It prints `Provider: openai_compatible`.
- It prints latency.
- It prints a non-empty response.
- It exits without an error.

## Step 8: Small Real System Test

```powershell
python main.py --users 20 --workers 4 --strategy round_robin --failures off
```

Success criteria:

- `Successful: 20 | Failed: 0`
- Per-worker stats show `providers [openai_compatible:...]`
- Workers receive roughly balanced work.

## Step 9: Real Fault-Tolerance Test

```powershell
$env:FAILURE_TRIGGER_TIME="1"
$env:FAILURE_RECOVERY_TIME="10"
$env:MAX_TASK_RETRIES="8"
$env:REASSIGNMENT_BACKOFF="0.5"

python main.py --users 50 --workers 4 --strategy round_robin --failures on
```

Success criteria:

- Worker failure is printed.
- Worker recovery is printed.
- Reassigned requests should be greater than 0.
- Final failed requests should be 0 or very low.

## Step 10: Final 1000-User Real LLM Test

```powershell
python main.py --users 1000 --workers 8 --strategy round_robin --failures off
```

If this succeeds, run the failure version:

```powershell
python main.py --users 1000 --workers 8 --strategy round_robin --failures on
```

Success criteria for delivery:

- Provider is `openai_compatible`, not a simulator.
- 1000 total requests are generated.
- Success rate is at least 95%.
- Metrics show average latency, p95 latency, throughput, and per-worker counts.
- Failure test shows detection, reassignment, and recovery.

## If 1000 Is Too Slow

Do not switch to simulation. Keep it real and reduce generated tokens:

```powershell
$env:LLM_MAX_TOKENS="32"
```

Then retry:

```powershell
python main.py --users 1000 --workers 8 --strategy round_robin --failures off
```

If it still times out, reduce client concurrency while keeping 1000 total users:

```powershell
$env:CLIENT_CONCURRENCY_LIMIT="64"
$env:HTTP_CLIENT_THREADS="64"
python main.py --users 1000 --workers 8 --strategy round_robin --failures off
```

This is still a real 1000-request load test. It means 1000 requests are served
in controlled batches instead of all hitting the GPU at the exact same instant.
