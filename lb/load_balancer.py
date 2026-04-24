import threading


class LoadBalancer:
    def __init__(self, workers):
        if not workers:
            raise ValueError("LoadBalancer requires at least one worker")

        self.workers = workers
        self._index = 0
        self._lock = threading.Lock()

    def get_next_worker(self):
        with self._lock:
            worker = self.workers[self._index]
            self._index = (self._index + 1) % len(self.workers)
            return worker

    def dispatch(self, request):
        worker = self.get_next_worker()
        print(f"[LoadBalancer] Dispatching request {request.id} to worker {worker.id}")
        return worker.process(request)