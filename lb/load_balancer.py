import asyncio
import logging
import threading
from typing import Dict, Iterable, List, Optional

import config

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class LoadBalancer:
    def __init__(self, workers, strategy="round_robin"):
        if not workers:
            raise ValueError("LoadBalancer requires at least one worker")
        if strategy not in ("round_robin", "least_connections", "load_aware"):
            raise ValueError("strategy must be 'round_robin', 'least_connections', or 'load_aware'")

        self.workers = workers
        self.strategy = strategy
        self._index = 0
        self._lock = threading.Lock()

    def _active_workers(self, exclude: Optional[Iterable[int]] = None):
        excluded = set(exclude or [])
        return [
            worker
            for worker in self.workers
            if worker.id not in excluded and worker.is_active()
        ]

    def get_next_worker(self, exclude: Optional[Iterable[int]] = None):
        with self._lock:
            active_workers = self._active_workers(exclude=exclude)
            if not active_workers:
                raise RuntimeError("No active workers available")

            if self.strategy == "least_connections":
                return min(
                    active_workers,
                    key=lambda worker: (worker.get_active_connections(), worker.id),
                )

            if self.strategy == "load_aware":
                def worker_load(worker):
                    avg_latency = worker.get_average_latency()
                    latency_score = avg_latency if avg_latency > 0 else config.ROUTING_DEFAULT_LATENCY
                    return (
                        worker.get_utilization(),
                        worker.get_active_connections(),
                        latency_score,
                        worker.get_failed_count(),
                        worker.id,
                    )

                return min(active_workers, key=worker_load)

            total_workers = len(self.workers)
            for _ in range(total_workers):
                worker = self.workers[self._index]
                self._index = (self._index + 1) % total_workers
                if worker.id not in set(exclude or []) and worker.is_active():
                    return worker

            raise RuntimeError("No active workers available")

    async def dispatch_async(self, request):
        last_error = None
        excluded_for_current_cycle: List[int] = []
        max_attempts = max(len(self.workers), config.MAX_TASK_RETRIES)

        for attempt in range(max_attempts):
            try:
                worker = self.get_next_worker(exclude=excluded_for_current_cycle)
            except RuntimeError:
                excluded_for_current_cycle = []
                worker = self.get_next_worker()

            if not worker.start_request():
                excluded_for_current_cycle.append(worker.id)
                continue

            try:
                logger.info(
                    "Dispatching request %s to worker %s strategy=%s",
                    request.id,
                    worker.id,
                    self.strategy,
                )
                response = await worker.process_async(request)
                worker.finish_request(success=True, latency=response.latency)
                response.reassignments = attempt
                return response, attempt
            except Exception as exc:
                worker.finish_request(success=False)
                last_error = exc
                excluded_for_current_cycle.append(worker.id)
                logger.warning(
                    "Request %s failed on worker %s: %s",
                    request.id,
                    worker.id,
                    exc,
                )
                await asyncio.sleep(config.REASSIGNMENT_BACKOFF)

        if last_error is not None:
            raise RuntimeError(
                f"Request {request.id} could not be processed by any active worker"
            ) from last_error
        raise RuntimeError(f"Request {request.id} could not be dispatched")

    def dispatch(self, request):
        return asyncio.run(self.dispatch_async(request))

    def cluster_snapshot(self) -> List[Dict]:
        return [worker.status_snapshot() for worker in self.workers]
