import threading


class LoadBalancer:
    def __init__(self, workers, strategy="round_robin"):
        if not workers:
            raise ValueError("LoadBalancer requires at least one worker")
        if strategy not in ("round_robin", "least_connections"):
            raise ValueError("strategy must be 'round_robin' or 'least_connections'")

        self.workers = workers
        self.strategy = strategy
        self._index = 0
        self._lock = threading.Lock()

    def _active_workers(self):
        active = [worker for worker in self.workers if worker.is_active()]
        inactive = [worker for worker in self.workers if not worker.is_active()]
        for worker in inactive:
            print(f"[LoadBalancer] Skipping failed worker {worker.id}")
        return active

    def get_next_worker(self):
        with self._lock:
            active_workers = self._active_workers()
            if not active_workers:
                raise RuntimeError("No active workers available")

            if self.strategy == "least_connections":
                return min(
                    active_workers,
                    key=lambda worker: (worker.get_active_connections(), worker.id),
                )

            total_workers = len(self.workers)
            for _ in range(total_workers):
                worker = self.workers[self._index]
                self._index = (self._index + 1) % total_workers
                if worker.is_active():
                    return worker

            raise RuntimeError("No active workers available")

    def dispatch(self, request):
        last_error = None

        for attempt in range(len(self.workers)):
            worker = self.get_next_worker()
            if not worker.start_request():
                print(
                    f"[LoadBalancer] Worker {worker.id} became inactive before "
                    f"request {request.id} dispatch"
                )
                continue

            try:
                print(
                    f"[LoadBalancer] Dispatching request {request.id} to worker "
                    f"{worker.id} using {self.strategy}"
                )
                response = worker.process(request)
                worker.finish_request(success=True)
                return response, attempt
            except Exception as exc:
                worker.finish_request(success=False)
                last_error = exc
                print(
                    f"[LoadBalancer] Request {request.id} failed on worker "
                    f"{worker.id}: {exc}"
                )
                if attempt < len(self.workers) - 1:
                    print(
                        f"[LoadBalancer] Reassigning request {request.id} "
                        f"to another active worker"
                    )

        if last_error is not None:
            raise RuntimeError(
                f"Request {request.id} could not be processed by any active worker"
            ) from last_error
        raise RuntimeError(f"Request {request.id} could not be dispatched")