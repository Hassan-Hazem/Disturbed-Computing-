import asyncio
import logging
import threading
import time
from typing import Dict

import config
from common.models import Response
from llm.inference import run_llm_async
from rag.retriever import retrieve_context_async

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class GPUWorker:
    def __init__(self, worker_id, max_parallelism=None):
        self.id = worker_id
        self.max_parallelism = max_parallelism or config.WORKER_PARALLELISM
        self.active = True
        self.active_connections = 0
        self.processed_count = 0
        self.failed_count = 0
        self.total_latency = 0.0
        self.last_heartbeat = time.time()
        self._capacity = asyncio.Semaphore(self.max_parallelism)
        self._lock = threading.Lock()

    def fail(self):
        with self._lock:
            self.active = False
            self.last_heartbeat = time.time()
        logger.warning("Worker %s failed", self.id)
        print(f"[Worker {self.id}] FAILURE simulated; worker marked inactive")

    def recover(self):
        with self._lock:
            self.active = True
            self.last_heartbeat = time.time()
        logger.info("Worker %s recovered", self.id)
        print(f"[Worker {self.id}] RECOVERY complete; worker marked active")

    def heartbeat(self):
        with self._lock:
            self.last_heartbeat = time.time()

    def is_active(self):
        with self._lock:
            return self.active

    def get_active_connections(self):
        with self._lock:
            return self.active_connections

    def get_processed_count(self):
        with self._lock:
            return self.processed_count

    def get_average_latency(self):
        with self._lock:
            if self.processed_count == 0:
                return 0.0
            return self.total_latency / self.processed_count

    def get_utilization(self):
        with self._lock:
            return min(1.0, self.active_connections / max(1, self.max_parallelism))

    def get_failed_count(self):
        with self._lock:
            return self.failed_count

    def start_request(self):
        with self._lock:
            if not self.active:
                return False
            self.active_connections += 1
            self.last_heartbeat = time.time()
            return True

    def finish_request(self, success=True, latency=0.0):
        with self._lock:
            if self.active_connections > 0:
                self.active_connections -= 1
            if success:
                self.processed_count += 1
                self.total_latency += latency
            else:
                self.failed_count += 1
            self.last_heartbeat = time.time()

    def status_snapshot(self) -> Dict:
        with self._lock:
            avg_latency = self.total_latency / self.processed_count if self.processed_count else 0.0
            return {
                "id": self.id,
                "active": self.active,
                "active_connections": self.active_connections,
                "capacity": self.max_parallelism,
                "utilization": min(1.0, self.active_connections / max(1, self.max_parallelism)),
                "processed": self.processed_count,
                "failures": self.failed_count,
                "avg_latency": avg_latency,
                "last_heartbeat": self.last_heartbeat,
            }

    async def process_async(self, request):
        if not self.is_active():
            raise RuntimeError(f"Worker {self.id} is inactive")

        async with self._capacity:
            if not self.is_active():
                raise RuntimeError(f"Worker {self.id} became inactive before processing")

            logger.info("Worker %s processing request %s", self.id, request.id)
            start_time = time.perf_counter()

            if config.WORKER_LOCAL_OVERHEAD > 0:
                await asyncio.sleep(config.WORKER_LOCAL_OVERHEAD)
            context = await retrieve_context_async(request.query)
            llm_result = await run_llm_async(request.query, context)

            if not self.is_active():
                raise RuntimeError(
                    f"Worker {self.id} failed during processing of request {request.id}"
                )

            latency = time.perf_counter() - start_time
            logger.info(
                "Worker %s finished request %s latency=%.3fs provider=%s",
                self.id,
                request.id,
                latency,
                llm_result.provider,
            )
            return Response(
                id=request.id,
                result=llm_result.text,
                latency=latency,
                worker_id=self.id,
                provider=llm_result.provider,
                context=context,
            )

    def process(self, request):
        """Synchronous compatibility wrapper for older call sites."""
        return asyncio.run(self.process_async(request))
