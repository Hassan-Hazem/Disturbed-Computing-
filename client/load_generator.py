import threading

from common.models import Request


def simulate_user(scheduler, user_id):
    request = Request(id=user_id, query=f"User query {user_id}")
    response = scheduler.handle_request(request)
    print(
        f"[Client] User {user_id} received response {response.id} "
        f"in {response.latency:.3f}s: {response.result}"
    )
    return response


def run_load_test(scheduler, num_users=1000):
    responses = []
    response_lock = threading.Lock()
    threads = []

    def user_thread(user_id):
        response = simulate_user(scheduler, user_id)
        with response_lock:
            responses.append(response)

    for user_id in range(1, num_users + 1):
        thread = threading.Thread(target=user_thread, args=(user_id,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    print(f"[Client] Completed load test for {len(responses)} users")
    return responses