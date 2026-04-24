import time
import threading

from common.models import Response
from llm.inference import run_llm
from rag.retriever import retrieve_context


class GPUWorker:
    def __init__(self, worker_id):
        self.id = worker_id
        self.active = True
        self.active_connections = 0
        self.processed_count = 0
        self._lock = threading.Lock()

    def fail(self):
        with self._lock:
            self.active = False
        print(f"[Worker {self.id}] FAILURE simulated; worker marked inactive")

    def recover(self):
        with self._lock:
            self.active = True
        print(f"[Worker {self.id}] RECOVERY complete; worker marked active")

    def is_active(self):
        with self._lock:
            return self.active

    def get_active_connections(self):
        with self._lock:
            return self.active_connections

    def start_request(self):
        with self._lock:
            if not self.active:
                return False
            self.active_connections += 1
            return True

    def finish_request(self, success=True):
        with self._lock:
            if self.active_connections > 0:
                self.active_connections -= 1
            if success:
                self.processed_count += 1

    def get_processed_count(self):
        with self._lock:
            return self.processed_count

    def process(self, request):
        if not self.is_active():
            raise RuntimeError(f"Worker {self.id} is inactive")

        print(f"[Worker {self.id}] Processing request {request.id}")
        start_time = time.time()

        context = retrieve_context(request.query)
        result = run_llm(request.query, context)

        if not self.is_active():
            raise RuntimeError(
                f"Worker {self.id} failed during processing of request {request.id}"
            )

        latency = time.time() - start_time
        print(f"[Worker {self.id}] Finished request {request.id} in {latency:.3f}s")
        return Response(id=request.id, result=result, latency=latency)