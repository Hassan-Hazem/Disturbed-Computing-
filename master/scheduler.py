class Scheduler:
    def __init__(self, load_balancer):
        self.load_balancer = load_balancer

    def handle_request(self, request):
        print(f"[Scheduler] Handling request {request.id}")
        return self.load_balancer.dispatch(request)