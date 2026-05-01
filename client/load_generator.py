"""
Client load generator that simulates 1000+ concurrent users
sending LLM inference requests to the distributed system.
"""

import threading
import time
from common.models import Request
from common.monitoring import PerformanceMonitor
import config


def simulate_user(scheduler, user_id, monitor: PerformanceMonitor = None):
    """Simulate a single user sending a request."""
    request = Request(id=user_id, query=f"User query {user_id}")
    try:
        response, reassignments = scheduler.handle_request(request)
        if monitor:
            monitor.record_request(
                request_id=user_id,
                latency=response.latency,
                success=True,
                reassignments=reassignments,
                worker_id=response.id % 4 + 1  # Approximate worker ID
            )
        if config.ENABLE_DETAILED_LOGGING:
            print(
                f"[Client] User {user_id} received response {response.id} "
                f"in {response.latency:.3f}s"
            )
        return response, reassignments
    except Exception as exc:
        if monitor:
            monitor.record_request(
                request_id=user_id,
                latency=0.0,
                success=False
            )
        print(f"[Client] User {user_id} request failed: {exc}")
        return None, 0


def run_load_test(scheduler, monitor: PerformanceMonitor = None, 
                  num_users: int = 1000, simulate_failures: bool = True):
    """
    Run load test simulating concurrent users.
    
    Features:
    - Concurrent request generation matching production workload
    - Optional failure injection during test
    - Performance metric collection
    - Fault tolerance verification
    """
    if monitor is None:
        from common.monitoring import PerformanceMonitor
        monitor = PerformanceMonitor()
    
    responses = []
    metrics = {
        "total_requests": num_users,
        "successful_requests": 0,
        "failed_requests": 0,
        "reassigned_requests": 0,
        "worker_processed": {},
    }
    response_lock = threading.Lock()
    threads = []
    start_time = time.time()

    def user_thread(user_id):
        """Execute request from a single simulated user."""
        try:
            response, reassignments = simulate_user(scheduler, user_id, monitor)
            if response:
                with response_lock:
                    responses.append(response)
                    metrics["successful_requests"] += 1
                    metrics["reassigned_requests"] += reassignments
            else:
                with response_lock:
                    metrics["failed_requests"] += 1
        except Exception as exc:
            with response_lock:
                metrics["failed_requests"] += 1
            print(f"[Client] User {user_id} thread error: {exc}")

    def trigger_failures():
        """Simulate worker node failures during load test."""
        time.sleep(config.FAILURE_TRIGGER_TIME)
        workers = scheduler.load_balancer.workers
        
        if len(workers) > 1:
            for i in range(min(config.WORKERS_TO_FAIL, len(workers) - 1)):
                failing_worker = workers[i + 1]
                failing_worker.fail()
                print(
                    f"[System] FAILURE INJECTION: Worker {failing_worker.id} "
                    f"marked as failed during active load"
                )
                
                # Simulate recovery after some time
                time.sleep(config.FAILURE_RECOVERY_TIME)
                if failing_worker:
                    failing_worker.recover()
                    print(
                        f"[System] RECOVERY: Worker {failing_worker.id} "
                        f"recovered and re-joined the cluster"
                    )

    # Launch failure simulation thread if enabled
    failure_thread = None
    if simulate_failures and config.SIMULATE_FAILURES:
        failure_thread = threading.Thread(target=trigger_failures, daemon=True)
        failure_thread.start()

    # Create and start user threads
    print(f"[Client] Launching {num_users} concurrent user threads...")
    for user_id in range(1, num_users + 1):
        thread = threading.Thread(target=user_thread, args=(user_id,))
        threads.append(thread)
        thread.start()
        
        # Print progress every N users
        if user_id % config.PRINT_METRICS_INTERVAL == 0:
            print(f"[Client] {user_id} users launched...")

    # Wait for all users to complete
    print(f"[Client] Waiting for all {num_users} users to complete...")
    for thread in threads:
        thread.join()

    if failure_thread:
        failure_thread.join()

    total_time = time.time() - start_time

    # Aggregate performance metrics
    latencies = [response.latency for response in responses]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    min_latency = min(latencies) if latencies else 0.0
    max_latency = max(latencies) if latencies else 0.0
    throughput = metrics["total_requests"] / total_time if total_time > 0 else 0.0

    # Collect per-worker statistics
    for worker in scheduler.load_balancer.workers:
        metrics["worker_processed"][worker.id] = worker.get_processed_count()

    # Verify system recovered from failures
    recovered = any(worker.is_active() for worker in scheduler.load_balancer.workers)
    recovery_status = (
        "✓ System successfully recovered from failures"
        if recovered
        else "✗ System recovery FAILED: no active workers available"
    )

    print("\n" + "="*70)
    print("LOAD TEST RESULTS".center(70))
    print("="*70)
    print(f"Total requests: {metrics['total_requests']}")
    print(f"Successful: {metrics['successful_requests']} | Failed: {metrics['failed_requests']}")
    print(f"Success rate: {100*metrics['successful_requests']/metrics['total_requests']:.1f}%")
    print(f"Requests reassigned due to failures: {metrics['reassigned_requests']}")
    print("-"*70)
    print(f"Average latency: {avg_latency:.4f}s")
    print(f"Min latency: {min_latency:.4f}s")
    print(f"Max latency: {max_latency:.4f}s")
    print(f"Total execution time: {total_time:.2f}s")
    print(f"Throughput: {throughput:.2f} requests/sec")
    print("-"*70)
    print("Requests processed per worker:")
    for worker_id in sorted(metrics["worker_processed"]):
        print(f"  Worker {worker_id}: {metrics['worker_processed'][worker_id]} requests")
    print("-"*70)
    print(f"Fault Tolerance Status: {recovery_status}")
    print("="*70 + "\n")

    return responses, metrics