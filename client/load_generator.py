"""
Async client load generator for 1000+ concurrent LLM requests.
"""

import asyncio
import logging
import time

import config
from common.models import Request
from common.monitoring import PerformanceMonitor

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


QUERY_TEMPLATES = [
    "Explain load balancing for distributed LLM inference",
    "How does fault tolerance prevent request loss in a worker cluster?",
    "Compare round robin and least connections scheduling",
    "Describe RAG for GPU backed LLM serving",
    "What metrics show worker utilization and throughput?",
]


async def simulate_user_async(scheduler, user_id, monitor: PerformanceMonitor = None):
    query = QUERY_TEMPLATES[user_id % len(QUERY_TEMPLATES)]
    request = Request(id=user_id, query=f"{query}. Request {user_id}")
    try:
        response, reassignments = await scheduler.handle_request_async(request)
        if monitor:
            monitor.record_request(
                request_id=user_id,
                latency=response.latency,
                success=True,
                reassignments=reassignments,
                worker_id=response.worker_id,
                provider=response.provider,
            )
        if config.ENABLE_DETAILED_LOGGING:
            print(
                f"[Client] User {user_id} received response {response.id} "
                f"from worker {response.worker_id} in {response.latency:.3f}s"
            )
        return response, reassignments
    except Exception as exc:
        if monitor:
            monitor.record_request(request_id=user_id, latency=0.0, success=False)
        logger.error("User %s request failed: %s", user_id, exc)
        if config.ENABLE_DETAILED_LOGGING:
            print(f"[Client] User {user_id} request failed: {exc}")
        return None, 0


def simulate_user(scheduler, user_id, monitor: PerformanceMonitor = None):
    return asyncio.run(simulate_user_async(scheduler, user_id, monitor))


async def run_load_test_async(
    scheduler,
    monitor: PerformanceMonitor = None,
    num_users: int = 1000,
    simulate_failures: bool = True,
):
    if monitor is None:
        monitor = PerformanceMonitor()

    responses = []
    metrics = {
        "total_requests": num_users,
        "successful_requests": 0,
        "failed_requests": 0,
        "reassigned_requests": 0,
        "worker_processed": {},
    }
    response_lock = asyncio.Lock()
    start_time = time.perf_counter()
    concurrency = min(num_users, max(1, config.CLIENT_CONCURRENCY_LIMIT))
    semaphore = asyncio.Semaphore(concurrency)

    async def guarded_user(user_id):
        async with semaphore:
            response, reassignments = await simulate_user_async(scheduler, user_id, monitor)
            async with response_lock:
                if response:
                    responses.append(response)
                    metrics["successful_requests"] += 1
                    metrics["reassigned_requests"] += reassignments
                else:
                    metrics["failed_requests"] += 1

    async def trigger_failures():
        await asyncio.sleep(config.FAILURE_TRIGGER_TIME)
        workers = scheduler.load_balancer.workers

        if len(workers) > 1:
            for i in range(min(config.WORKERS_TO_FAIL, len(workers) - 1)):
                failing_worker = workers[i + 1]
                failing_worker.fail()
                print(
                    f"[System] FAILURE INJECTION: Worker {failing_worker.id} "
                    f"marked as failed during active load"
                )
                await asyncio.sleep(config.FAILURE_RECOVERY_TIME)
                failing_worker.recover()
                print(
                    f"[System] RECOVERY: Worker {failing_worker.id} "
                    f"recovered and re-joined the cluster"
                )

    print(f"[Client] Launching {num_users} async users with concurrency limit {concurrency}...")

    failure_task = None
    if simulate_failures and config.SIMULATE_FAILURES:
        failure_task = asyncio.create_task(trigger_failures())

    tasks = []
    for user_id in range(1, num_users + 1):
        tasks.append(asyncio.create_task(guarded_user(user_id)))
        if user_id % config.PRINT_METRICS_INTERVAL == 0:
            print(f"[Client] {user_id} users scheduled...")

    print(f"[Client] Waiting for all {num_users} users to complete...")
    await asyncio.gather(*tasks)

    if failure_task:
        await failure_task

    total_time = time.perf_counter() - start_time

    latencies = [response.latency for response in responses]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    min_latency = min(latencies) if latencies else 0.0
    max_latency = max(latencies) if latencies else 0.0
    throughput = metrics["successful_requests"] / total_time if total_time > 0 else 0.0

    for worker in scheduler.load_balancer.workers:
        metrics["worker_processed"][worker.id] = worker.get_processed_count()

    active_workers = sum(1 for worker in scheduler.load_balancer.workers if worker.is_active())
    if simulate_failures and config.SIMULATE_FAILURES:
        recovery_status = (
            "System successfully recovered from failures"
            if active_workers > 0
            else "System recovery FAILED: no active workers available"
        )
    else:
        recovery_status = f"Failure simulation disabled; {active_workers} active workers available"

    print("\n" + "=" * 70)
    print("LOAD TEST RESULTS".center(70))
    print("=" * 70)
    print(f"Total requests: {metrics['total_requests']}")
    print(f"Successful: {metrics['successful_requests']} | Failed: {metrics['failed_requests']}")
    print(f"Success rate: {100 * metrics['successful_requests'] / metrics['total_requests']:.1f}%")
    print(f"Requests reassigned due to failures: {metrics['reassigned_requests']}")
    print("-" * 70)
    print(f"Average latency: {avg_latency:.4f}s")
    print(f"Min latency: {min_latency:.4f}s")
    print(f"Max latency: {max_latency:.4f}s")
    print(f"Total execution time: {total_time:.2f}s")
    print(f"Throughput: {throughput:.2f} successful requests/sec")
    print("-" * 70)
    print("Requests processed per worker:")
    for worker_id in sorted(metrics["worker_processed"]):
        print(f"  Worker {worker_id}: {metrics['worker_processed'][worker_id]} requests")
    print("-" * 70)
    print(f"Fault Tolerance Status: {recovery_status}")
    print("=" * 70 + "\n")

    return responses, metrics


def run_load_test(
    scheduler,
    monitor: PerformanceMonitor = None,
    num_users: int = 1000,
    simulate_failures: bool = True,
):
    return asyncio.run(run_load_test_async(scheduler, monitor, num_users, simulate_failures))
