"""
Performance monitoring module for distributed system metrics.
Tracks latency, throughput, resource utilization, and fault tolerance metrics.
"""

import time
from threading import Lock
from typing import Dict, List, Optional


class PerformanceMonitor:
    """Tracks and aggregates system performance metrics."""
    
    def __init__(self):
        self.lock = Lock()
        self.request_latencies: List[float] = []
        self.request_times: List[float] = []
        self.start_time = time.time()
        self.failed_requests = 0
        self.successful_requests = 0
        self.reassigned_requests = 0
        self.worker_stats: Dict[int, Dict] = {}
    
    def record_request(self, request_id: int, latency: float, success: bool,
                      reassignments: int = 0, worker_id: Optional[int] = None,
                      provider: str = "unknown"):
        """Record metrics for a completed request."""
        with self.lock:
            if success:
                self.request_latencies.append(latency)
                self.request_times.append(time.time() - self.start_time)
                self.successful_requests += 1
            else:
                self.failed_requests += 1
            
            self.reassigned_requests += reassignments
            
            if worker_id:
                if worker_id not in self.worker_stats:
                    self.worker_stats[worker_id] = {
                        'requests': 0,
                        'total_latency': 0.0,
                        'failures': 0,
                        'providers': {}
                    }
                self.worker_stats[worker_id]['requests'] += 1
                self.worker_stats[worker_id]['total_latency'] += latency
                providers = self.worker_stats[worker_id]['providers']
                providers[provider] = providers.get(provider, 0) + 1
    
    def get_statistics(self) -> Dict:
        """Get aggregated performance statistics."""
        with self.lock:
            elapsed_time = time.time() - self.start_time
            total_requests = self.successful_requests + self.failed_requests
            
            if not self.request_latencies:
                avg_latency = 0.0
                min_latency = 0.0
                max_latency = 0.0
                p95_latency = 0.0
            else:
                sorted_latencies = sorted(self.request_latencies)
                avg_latency = sum(self.request_latencies) / len(self.request_latencies)
                min_latency = min(self.request_latencies)
                max_latency = max(self.request_latencies)
                p95_index = int(len(sorted_latencies) * 0.95)
                p95_latency = sorted_latencies[p95_index] if p95_index < len(sorted_latencies) else max_latency
            
            throughput = total_requests / elapsed_time if elapsed_time > 0 else 0.0
            
            return {
                'elapsed_time': elapsed_time,
                'total_requests': total_requests,
                'successful_requests': self.successful_requests,
                'failed_requests': self.failed_requests,
                'reassigned_requests': self.reassigned_requests,
                'avg_latency': avg_latency,
                'min_latency': min_latency,
                'max_latency': max_latency,
                'p95_latency': p95_latency,
                'throughput': throughput,
                'worker_stats': self.worker_stats
            }
    
    def print_summary(self):
        """Print formatted performance summary."""
        stats = self.get_statistics()
        
        print("\n" + "="*60)
        print("DISTRIBUTED SYSTEM PERFORMANCE METRICS".center(60))
        print("="*60)
        print(f"Total Requests: {stats['total_requests']}")
        print(f"Successful: {stats['successful_requests']} | Failed: {stats['failed_requests']}")
        print(f"Reassigned: {stats['reassigned_requests']}")
        print("-"*60)
        print(f"Avg Latency: {stats['avg_latency']:.4f}s")
        print(f"Min Latency: {stats['min_latency']:.4f}s")
        print(f"Max Latency: {stats['max_latency']:.4f}s")
        print(f"P95 Latency: {stats['p95_latency']:.4f}s")
        print("-"*60)
        print(f"Throughput: {stats['throughput']:.2f} requests/sec")
        print(f"Total Execution Time: {stats['elapsed_time']:.4f}s")
        print("-"*60)
        
        if stats['worker_stats']:
            print("Per-Worker Statistics:")
            for worker_id in sorted(stats['worker_stats'].keys()):
                ws = stats['worker_stats'][worker_id]
                avg_w_latency = ws['total_latency'] / ws['requests'] if ws['requests'] > 0 else 0
                providers = ", ".join(
                    f"{provider}:{count}" for provider, count in sorted(ws.get('providers', {}).items())
                )
                print(f"  Worker {worker_id}: {ws['requests']} requests, "
                      f"avg latency {avg_w_latency:.4f}s, providers [{providers}]")
        print("="*60 + "\n")
