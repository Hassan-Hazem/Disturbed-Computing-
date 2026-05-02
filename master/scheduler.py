import asyncio
import logging
import threading
import time
from typing import Dict

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class Scheduler:
    def __init__(self, load_balancer):
        self.load_balancer = load_balancer
        self._lock = threading.Lock()
        self._inflight: Dict[int, float] = {}
        self._completed = 0
        self._failed = 0
        self._reassigned = 0

    async def handle_request_async(self, request):
        with self._lock:
            self._inflight[request.id] = time.time()

        logger.info("Scheduler received request %s", request.id)
        try:
            response, reassignments = await self.load_balancer.dispatch_async(request)
            with self._lock:
                self._completed += 1
                self._reassigned += reassignments
                self._inflight.pop(request.id, None)
            if reassignments > 0:
                logger.info("Request %s reassigned %s time(s)", request.id, reassignments)
            return response, reassignments
        except Exception:
            with self._lock:
                self._failed += 1
                self._inflight.pop(request.id, None)
            raise

    def handle_request(self, request):
        return asyncio.run(self.handle_request_async(request))

    def metrics(self):
        with self._lock:
            return {
                "inflight": len(self._inflight),
                "completed": self._completed,
                "failed": self._failed,
                "reassigned": self._reassigned,
                "workers": self.load_balancer.cluster_snapshot(),
            }

    def print_worker_status(self):
        snapshot = self.metrics()["workers"]
        print("\nWorker status:")
        for worker in snapshot:
            state = "active" if worker["active"] else "failed"
            print(
                f"  Worker {worker['id']}: {state}, "
                f"active={worker['active_connections']}/{worker['capacity']}, "
                f"processed={worker['processed']}, "
                f"avg_latency={worker['avg_latency']:.3f}s"
            )
