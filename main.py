from client.load_generator import run_load_test
from lb.load_balancer import LoadBalancer
from master.scheduler import Scheduler
from workers.gpu_worker import GPUWorker


def main() -> None:
    workers = [GPUWorker(worker_id=index + 1) for index in range(4)]
    load_balancer = LoadBalancer(workers, strategy="round_robin")
    scheduler = Scheduler(load_balancer)
    run_load_test(scheduler, num_users=1000)


if __name__ == "__main__":
    main()