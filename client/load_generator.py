import threading
import time

from common.models import Request


def simulate_user(scheduler, user_id):
    request = Request(id=user_id, query=f"User query {user_id}")
    response, reassignments = scheduler.handle_request(request)
    print(
        f"[Client] User {user_id} received response {response.id} "
        f"in {response.latency:.3f}s: {response.result}"
    )
    return response, reassignments


def run_load_test(scheduler, num_users=1000):
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
        try:
            response, reassignments = simulate_user(scheduler, user_id)
            with response_lock:
                responses.append(response)
                metrics["successful_requests"] += 1
                metrics["reassigned_requests"] += reassignments
        except Exception as exc:
            with response_lock:
                metrics["failed_requests"] += 1
            print(f"[Client] User {user_id} request failed: {exc}")

    def trigger_failure():
        time.sleep(0.05)
        if len(scheduler.load_balancer.workers) > 1:
            failing_worker = scheduler.load_balancer.workers[1]
            failing_worker.fail()
            print(
                "[Client] Failure simulation triggered: "
                f"Worker {failing_worker.id} was failed during active load"
            )

    failure_thread = threading.Thread(target=trigger_failure)
    failure_thread.start()

    for user_id in range(1, num_users + 1):
        thread = threading.Thread(target=user_thread, args=(user_id,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    failure_thread.join()

    total_time = time.time() - start_time
    latencies = [response.latency for response in responses]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    min_latency = min(latencies) if latencies else 0.0
    max_latency = max(latencies) if latencies else 0.0
    throughput = metrics["total_requests"] / total_time if total_time > 0 else 0.0

    for worker in scheduler.load_balancer.workers:
        metrics["worker_processed"][worker.id] = worker.get_processed_count()

    recovered = any(worker.is_active() for worker in scheduler.load_balancer.workers)
    recovery_msg = (
        "System recovered: requests continued on active workers after failure"
        if recovered
        else "System recovery failed: no active workers available"
    )

    print("\n=== FINAL PERFORMANCE METRICS ===")
    print(f"Total requests: {metrics['total_requests']}")
    print(f"Successful requests: {metrics['successful_requests']}")
    print(f"Failed requests: {metrics['failed_requests']}")
    print(f"Reassigned requests: {metrics['reassigned_requests']}")
    print(f"Average latency: {avg_latency:.4f}s")
    print(f"Minimum latency: {min_latency:.4f}s")
    print(f"Maximum latency: {max_latency:.4f}s")
    print(f"Total execution time: {total_time:.4f}s")
    print(f"Throughput: {throughput:.2f} requests/sec")
    print("Requests processed per worker:")
    for worker_id in sorted(metrics["worker_processed"]):
        print(f"  Worker {worker_id}: {metrics['worker_processed'][worker_id]}")
    print(f"Final confirmation: {recovery_msg}")

    print(f"[Client] Completed load test for {len(responses)} users")
    return responses, metrics