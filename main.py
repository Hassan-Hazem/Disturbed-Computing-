"""
Main entry point for Distributed LLM System with Load Balancing and Fault Tolerance.

This system demonstrates:
- Load balancing with multiple strategies (Round Robin, Least Connections, Load-Aware)
- GPU worker cluster management
- LLM inference with RAG integration
- Fault tolerance with automatic task reassignment
- Performance monitoring and metrics collection
- Scalability to 1000+ concurrent users

To run with different configurations, modify config.py or pass arguments to main().
"""

import argparse
import logging

from client.load_generator import run_load_test
from lb.load_balancer import LoadBalancer
from master.scheduler import Scheduler
from workers.gpu_worker import GPUWorker
from common.monitoring import PerformanceMonitor
import config


def configure_logging() -> None:
    file_handler = logging.FileHandler(config.LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    handlers = [file_handler]
    if config.ENABLE_DETAILED_LOGGING:
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        handlers.append(stream_handler)

    root = logging.getLogger()
    root.handlers.clear()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=handlers,
    )


def main(
    num_workers: int = None,
    num_users: int = None,
    strategy: str = None,
    simulate_failures: bool = None
) -> None:
    """
    Main execution function with configurable parameters.
    
    Args:
        num_workers: Number of GPU worker nodes (default from config)
        num_users: Number of concurrent users (default from config)
        strategy: Load balancing strategy (default from config)
        simulate_failures: Whether to simulate node failures (default from config)
    """
    configure_logging()

    num_workers = num_workers or config.NUM_WORKERS
    num_users = num_users or config.NUM_USERS
    strategy = strategy or config.LOAD_BALANCING_STRATEGY
    simulate_failures = simulate_failures if simulate_failures is not None else config.SIMULATE_FAILURES
    
    print("\n" + "="*70)
    print("DISTRIBUTED LLM SYSTEM - Load Balancing & Fault Tolerance".center(70))
    print("="*70)
    print(f"Configuration:")
    print(f"  - Workers: {num_workers}")
    print(f"  - Users: {num_users}")
    print(f"  - Strategy: {strategy}")
    print(f"  - Failure Simulation: {simulate_failures}")
    print(f"  - LLM Provider: {config.LLM_PROVIDER}")
    print(f"  - Worker Parallelism: {config.WORKER_PARALLELISM}")
    print("="*70 + "\n")
    
    workers = [GPUWorker(worker_id=i + 1) for i in range(num_workers)]
    load_balancer = LoadBalancer(workers, strategy=strategy)
    scheduler = Scheduler(load_balancer)
    monitor = PerformanceMonitor()
    
    print(f"[System] Initialized {num_workers} GPU worker nodes")
    print(f"[System] Load balancer using '{strategy}' strategy\n")
    
    # Run load test
    responses, metrics = run_load_test(
        scheduler,
        monitor,
        num_users=num_users,
        simulate_failures=simulate_failures
    )
    
    # Print performance summary
    monitor.print_summary()
    
    # Additional metrics from load test
    print("Load Test Metrics:")
    print(f"  - Total requests generated: {metrics['total_requests']}")
    print(f"  - Successfully completed: {metrics['successful_requests']}")
    print(f"  - Failed: {metrics['failed_requests']}")
    print(f"  - Reassigned due to failures: {metrics['reassigned_requests']}")
    
    if metrics['worker_processed']:
        print("\nRequests processed per worker:")
        for worker_id in sorted(metrics['worker_processed'].keys()):
            count = metrics['worker_processed'][worker_id]
            print(f"  - Worker {worker_id}: {count} requests")

    scheduler.print_worker_status()


def parse_args():
    parser = argparse.ArgumentParser(description="Distributed LLM load-balancing demo")
    parser.add_argument("--workers", type=int, default=None, help="Number of GPU workers")
    parser.add_argument("--users", type=int, default=None, help="Number of concurrent users")
    parser.add_argument(
        "--strategy",
        choices=["round_robin", "least_connections", "load_aware"],
        default=None,
        help="Load-balancing strategy",
    )
    parser.add_argument(
        "--failures",
        choices=["on", "off"],
        default=None,
        help="Enable or disable worker failure simulation",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    failures = None if args.failures is None else args.failures == "on"
    main(
        num_workers=args.workers,
        num_users=args.users,
        strategy=args.strategy,
        simulate_failures=failures,
    )
