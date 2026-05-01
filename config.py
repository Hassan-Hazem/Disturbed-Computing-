# Configuration file for Distributed LLM System
# Adjust parameters here for different scenarios

# System Configuration
NUM_WORKERS = 4  # Number of GPU worker nodes
NUM_USERS = 1000  # Number of concurrent users to simulate
LOAD_BALANCING_STRATEGY = "load_aware"  # Options: "round_robin", "least_connections", "load_aware"

# Failure Simulation
SIMULATE_FAILURES = True  # Enable failure simulation during load test
FAILURE_TRIGGER_TIME = 0.05  # Seconds to wait before triggering first failure
FAILURE_RECOVERY_TIME = 2.0  # Time in seconds before worker can recover
WORKERS_TO_FAIL = 1  # Number of workers to fail during test

# Performance Settings
LLM_BASE_LATENCY = 0.15  # Base LLM inference latency in seconds
LLM_VARIANCE = 0.1  # Random variance in latency
QUERY_COMPLEXITY_FACTOR = 0.02  # Latency factor per query word

# Monitoring
ENABLE_DETAILED_LOGGING = False  # Enable detailed console output (disable for large tests)
COLLECT_PERFORMANCE_METRICS = True  # Collect and display performance metrics
PRINT_METRICS_INTERVAL = 100  # Print metrics every N requests
