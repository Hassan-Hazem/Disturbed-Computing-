class Scheduler:
    def __init__(self, load_balancer):
        self.load_balancer = load_balancer

    def handle_request(self, request):
        print(f"[Scheduler] Handling request {request.id}")
        response, reassignments = self.load_balancer.dispatch(request)
        if reassignments > 0:
            print(
                f"[Scheduler] Request {request.id} reassigned {reassignments} "
                "time(s) before completion"
            )
        return response, reassignments