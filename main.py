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

from client.load_generator import run_load_test
from lb.load_balancer import LoadBalancer
from master.scheduler import Scheduler
from workers.gpu_worker import GPUWorker
from common.monitoring import PerformanceMonitor
import config


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
    # Use provided args or fall back to config
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
    print("="*70 + "\n")
    
    # Initialize system components
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


if __name__ == "__main__":
    # Run with default configuration from config.py
    main()
    
    # Uncomment below to test with different strategies:
    # main(strategy="round_robin", num_users=100)
    # main(strategy="least_connections", num_users=100)
    # main(strategy="load_aware", num_users=100)