import time

from common.models import Response
from llm.inference import run_llm
from rag.retriever import retrieve_context


class GPUWorker:
    def __init__(self, worker_id):
        self.id = worker_id

    def process(self, request):
        print(f"[Worker {self.id}] Processing request {request.id}")
        start_time = time.time()

        context = retrieve_context(request.query)
        result = run_llm(request.query, context)

        latency = time.time() - start_time
        print(f"[Worker {self.id}] Finished request {request.id} in {latency:.3f}s")
        return Response(id=request.id, result=result, latency=latency)