"""
Quick test script to verify the system works with smaller load.
"""

from client.load_generator import run_load_test
from lb.load_balancer import LoadBalancer
from master.scheduler import Scheduler
from workers.gpu_worker import GPUWorker
from common.monitoring import PerformanceMonitor

# Create system components
workers = [GPUWorker(worker_id=i + 1) for i in range(4)]
load_balancer = LoadBalancer(workers, strategy="load_aware")
scheduler = Scheduler(load_balancer)
monitor = PerformanceMonitor()

print("\n" + "="*70)
print("QUICK TEST - 100 Users, Load-Aware Strategy, Failure Simulation")
print("="*70 + "\n")

# Run smaller test
responses, metrics = run_load_test(
    scheduler,
    monitor,
    num_users=100,
    simulate_failures=True
)

# Print summary
monitor.print_summary()
