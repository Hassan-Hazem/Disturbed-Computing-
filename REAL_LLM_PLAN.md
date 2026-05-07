# Real LLM Execution Plan

## Recommended Choice

Use Ollama as the primary provider for the two-laptop demo.

Why:

- It runs locally, so there is no per-request API cost.
- It is easy to explain in a distributed systems project: one laptop can be the LLM server, and the other can be a client/load-generator or second worker machine.
- It avoids cloud rate limits during the 1000-user demo.
- The project already supports remote Ollama through `OLLAMA_BASE_URL`.

Use OpenRouter as backup for a quick internet-based real LLM proof. Use Thunder Compute only for the final GPU benchmark if the laptops are too slow. LM Studio is useful for manual local testing, but Ollama is better for repeatable command-line demos.

## Two-Laptop Ollama Setup

Laptop A is the model server.

```powershell
ollama pull llama3.1:8b
$env:OLLAMA_HOST="0.0.0.0:11434"
ollama serve
```

Find Laptop A IP:

```powershell
ipconfig
```

Laptop B runs the project and points to Laptop A:

```powershell
$env:LLM_PROVIDER="ollama"
$env:OLLAMA_BASE_URL="http://LAPTOP_A_IP:11434"
$env:OLLAMA_MODEL="llama3.1:8b"
$env:ALLOW_SIMULATED_LLM="false"
python test_real_llm_provider.py
```

If this succeeds, run a small distributed test:

```powershell
python main.py --users 20 --workers 2 --strategy load_aware --failures off
```

Then run the project demo:

```powershell
python main.py --users 100 --workers 4 --strategy load_aware --failures on
```

Use 1000 users only after the smaller real-model tests pass:

```powershell
python main.py --users 1000 --workers 4 --strategy load_aware --failures on
```

## OpenRouter Backup

```powershell
$env:LLM_PROVIDER="openrouter"
$env:OPENROUTER_API_KEY="YOUR_KEY"
$env:OPENROUTER_MODEL="openrouter/free"
$env:ALLOW_SIMULATED_LLM="false"
python test_real_llm_provider.py
```

Then:

```powershell
python main.py --users 20 --workers 2 --strategy load_aware --failures off
```

## LM Studio Option

Start LM Studio local server, then:

```powershell
$env:LLM_PROVIDER="lmstudio"
$env:LMSTUDIO_BASE_URL="http://localhost:1234/v1"
$env:LMSTUDIO_MODEL="local-model"
$env:ALLOW_SIMULATED_LLM="false"
python test_real_llm_provider.py
```

## Thunder Compute Option

Use Thunder Compute if you want a stronger final benchmark with a rented GPU. The easiest path is to run either Ollama or a vLLM OpenAI-compatible server on the GPU node.

For an Ollama server on the GPU node:

```powershell
$env:LLM_PROVIDER="ollama"
$env:OLLAMA_BASE_URL="http://THUNDER_NODE_IP:11434"
$env:OLLAMA_MODEL="llama3.1:8b"
$env:ALLOW_SIMULATED_LLM="false"
python test_real_llm_provider.py
```

For a vLLM/OpenAI-compatible server:

```powershell
$env:LLM_PROVIDER="openai_compatible"
$env:OPENAI_COMPATIBLE_BASE_URL="http://THUNDER_NODE_IP:8000/v1"
$env:OPENAI_COMPATIBLE_MODEL="MODEL_NAME"
$env:OPENAI_COMPATIBLE_API_KEY=""
$env:ALLOW_SIMULATED_LLM="false"
python test_real_llm_provider.py
```

## Success Criteria

Provider smoke test:

- `python test_real_llm_provider.py` exits with code 0.
- Output says `Provider: ollama`, `Provider: openrouter`, `Provider: lmstudio`, or `Provider: openai_compatible`.
- Output must not say `Provider: simulated`.
- Response text is non-empty.
- Latency is printed.

Small real-model system test:

- `python main.py --users 20 --failures off` completes.
- Successful requests equal total requests.
- Failed requests equal 0.
- Per-worker metrics show real provider name, not simulated.

Fault-tolerance test:

- `python main.py --users 100 --failures on` completes.
- At least one worker failure is printed.
- Reassigned requests is greater than 0.
- Final failed requests is 0 if at least one healthy worker remains.

Final demo test:

- 1000 requests complete.
- Success rate is at least 95%.
- No simulated provider is used.
- Metrics include average latency, p95 latency, throughput, reassignments, and worker status.
