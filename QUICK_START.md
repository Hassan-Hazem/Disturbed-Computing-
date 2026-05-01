# QUICK START GUIDE

## System Requirements
- Python 3.9+
- No external dependencies (uses only Python standard library)

## How to Run

### 1. Default Execution (1000 users, load-aware strategy)
```bash
cd "d:\uni\SPRING 26\Distributed Computing\Project"
python main.py
```

**Output**: Complete performance metrics showing:
- 1000 concurrent users processed
- Load distribution across 4 workers
- Fault tolerance with automatic recovery
- Latency and throughput statistics

### 2. Quick Test (100 users with detailed output)
```bash
python test_quick.py
```

**Output**: Detailed logs showing:
- Every request dispatch and processing
- Worker failure injection at 0.05s
- Automatic task reassignment
- Worker recovery after 2 seconds
- All 100 requests completed successfully (100% success rate)

### 3. Strategy Comparison Test
```bash
python test_strategies.py
```

**Tests each strategy**:
- Round Robin: Fair distribution
- Least Connections: Considers active load
- Load-Aware: Optimal performance (recommended)

## Configuration

Edit `config.py` to customize:

```python
NUM_WORKERS = 4                        # Change number of workers
NUM_USERS = 1000                       # Change user count
LOAD_BALANCING_STRATEGY = "load_aware" # Choose strategy
SIMULATE_FAILURES = True               # Enable/disable failures
ENABLE_DETAILED_LOGGING = True         # For small tests only
```

## Project Structure

```
Project/
├── main.py                 # Entry point
├── config.py              # Configuration (modify this!)
├── README.md              # Full documentation
├── REQUIREMENTS_CHECKLIST.md  # PDF requirements verification
├── QUICK_START.md         # This file
│
├── client/
│   └── load_generator.py  # 1000+ user simulation
├── lb/
│   └── load_balancer.py   # Round Robin, Least Connections, Load-Aware
├── master/
│   └── scheduler.py       # Request scheduling
├── workers/
│   └── gpu_worker.py      # GPU worker nodes with failure handling
├── llm/
│   └── inference.py       # LLM inference simulation
├── rag/
│   └── retriever.py       # Knowledge base & context retrieval
├── common/
│   ├── models.py          # Request/Response data models
│   └── monitoring.py      # Performance metrics collection
│
└── test_quick.py          # Quick test with 100 users
└── test_strategies.py     # Strategy comparison test
```

## Key Features Implemented

✅ **Load Balancing** (3 strategies)
- Round Robin
- Least Connections  
- Load-Aware (recommended)

✅ **Scalability**
- 1000+ concurrent users
- Configurable workers
- Linear performance scaling

✅ **Fault Tolerance**
- Worker failure detection
- Automatic task reassignment
- Worker recovery

✅ **Performance Monitoring**
- Latency tracking (avg, min, max, p95)
- Throughput measurement
- Per-worker statistics
- Real-time metrics

✅ **RAG Integration**
- 20+ concept knowledge base
- Semantic context retrieval
- Fallback context generation

## Expected Output Example

### 100-User Test (from test_quick.py):
```
======================================================================
QUICK TEST - 100 Users, Load-Aware Strategy, Failure Simulation
======================================================================

[Client] Launching 100 concurrent user threads...
[System] FAILURE INJECTION: Worker 2 marked as failed during active load
[LoadBalancer] Reassigning request 75 to another active worker
[System] RECOVERY: Worker 2 recovered and re-joined the cluster

======================================================================
                          LOAD TEST RESULTS                           
======================================================================
Total requests: 100
Successful: 100 | Failed: 0
Success rate: 100.0%
Requests reassigned due to failures: 25
----------------------------------------------------------------------
Average latency: 0.2634s
Min latency: 0.2105s
Max latency: 0.3104s
Total execution time: 2.05s
Throughput: 48.71 requests/sec
----------------------------------------------------------------------
Fault Tolerance Status: ✓ System successfully recovered from failures
======================================================================
```

## Common Modifications

### Test with Different Number of Workers
```python
# In main.py, change:
NUM_WORKERS = 8  # More workers = higher throughput
```

### Test Specific Strategy
```python
# In config.py, change:
LOAD_BALANCING_STRATEGY = "round_robin"      # Simple fairness
LOAD_BALANCING_STRATEGY = "least_connections" # Load-aware
LOAD_BALANCING_STRATEGY = "load_aware"        # Optimal (recommended)
```

### Disable Failure Simulation
```python
# In config.py, change:
SIMULATE_FAILURES = False  # No failure injection
```

### Smaller Load Test
```python
# In config.py, change:
NUM_USERS = 100  # Smaller load
ENABLE_DETAILED_LOGGING = True  # See detailed logs
```

## Troubleshooting

### "No module named 'config'"
- Ensure you're running from project root directory
- Check that `config.py` exists

### Very Slow Execution
- Disable `ENABLE_DETAILED_LOGGING` in `config.py` for 1000+ users
- Reduce `NUM_USERS` to test faster

### All workers becoming inactive
- This means all workers failed (shouldn't happen unless FAILURE_RECOVERY_TIME is very long)
- Check that at least one worker stays active

## Learning Outcomes

This project demonstrates:
- Distributed systems design and implementation
- Load balancing algorithms and strategies
- Horizontal scaling techniques
- Fault tolerance mechanisms
- Real-time performance monitoring
- Concurrent request processing
- GPU cluster management

## Next Steps for Enhancement

1. Add real LLM model integration (HuggingFace, OpenAI)
2. Implement gRPC for distributed communication
3. Add persistent logging and telemetry
4. Integrate with Kubernetes for orchestration
5. Add circuit breaker pattern for cascading failure prevention
6. Dynamic worker scaling based on load
7. Advanced scheduling algorithms (FIFO, Priority Queue)

---

**Ready to run!** Execute `python main.py` to see the distributed system in action.
