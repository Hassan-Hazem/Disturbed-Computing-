"""
Test script to compare different load balancing strategies.
Demonstrates all three strategies implemented in the project.
"""

from client.load_generator import run_load_test
from lb.load_balancer import LoadBalancer
from master.scheduler import Scheduler
from workers.gpu_worker import GPUWorker
from common.monitoring import PerformanceMonitor


def test_strategy(strategy_name: str, num_users: int = 50):
    """Test a single load balancing strategy."""
    print(f"\n{'='*70}")
    print(f"Testing Strategy: {strategy_name.upper()} ({num_users} users)")
    print('='*70)
    
    # Create system components
    workers = [GPUWorker(worker_id=i + 1) for i in range(4)]
    load_balancer = LoadBalancer(workers, strategy=strategy_name)
    scheduler = Scheduler(load_balancer)
    monitor = PerformanceMonitor()
    
    # Run load test
    responses, metrics = run_load_test(
        scheduler,
        monitor,
        num_users=num_users,
        simulate_failures=False  # No failures for clean comparison
    )
    
    # Print summary
    stats = monitor.get_statistics()
    print("\nStrategy Results:")
    print(f"  - Success Rate: {100*metrics['successful_requests']/metrics['total_requests']:.1f}%")
    print(f"  - Avg Latency: {stats['avg_latency']:.4f}s")
    print(f"  - Max Latency: {stats['max_latency']:.4f}s")
    print(f"  - Throughput: {stats['throughput']:.2f} requests/sec")
    
    if stats['worker_stats']:
        print("  - Load Distribution:")
        for worker_id in sorted(stats['worker_stats'].keys()):
            ws = stats['worker_stats'][worker_id]
            print(f"      Worker {worker_id}: {ws['requests']} requests")


if __name__ == "__main__":
    print("\nSTRATEGY COMPARISON TEST")
    print("Testing load balancing strategies with 50 users each")
    
    # Test all three strategies
    test_strategy("round_robin", num_users=50)
    test_strategy("least_connections", num_users=50)
    test_strategy("load_aware", num_users=50)
    
    print(f"\n{'='*70}")
    print("COMPARISON COMPLETE")
    print("load_aware strategy optimizes for balanced load and worker efficiency")
    print('='*70 + "\n")
