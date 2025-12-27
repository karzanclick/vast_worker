import os
import random
import string

from vastai import (
    Worker,
    WorkerConfig,
    HandlerConfig,
    LogActionConfig,
    BenchmarkConfig,
)

# --- Model configuration ------------------------------------------------------

MODEL_SERVER_URL = "http://127.0.0.1"
MODEL_SERVER_PORT = 18000
MODEL_LOG_FILE = "/var/log/model/server.log"

# Log messages to detect model ready state
MODEL_LOAD_LOG_MSG = [
    "Application startup complete.",
    "Model loaded successfully",
]

MODEL_ERROR_LOG_MSGS = [
    "INFO exited:",
    "RuntimeError: Engine",
    "Traceback (most recent call last):",
    "ERROR:",
]

MODEL_INFO_LOG_MSGS = [
    '"message":"Download',
    "INFO:",
]

# --- Benchmark data generation -----------------------------------------------

def generate_random_text(length: int = 250) -> str:
    """Generate random text for testing."""
    words = [''.join(random.choices(string.ascii_lowercase, k=random.randint(3, 10))) 
             for _ in range(length)]
    return " ".join(words)

def completions_benchmark_generator() -> dict:
    """Generate one benchmark payload for the /v1/completions endpoint."""
    prompt = generate_random_text(250)
    
    model = os.environ.get("MODEL_NAME", "test-model")
    
    return {
        "model": model,
        "prompt": prompt,
        "temperature": 0.7,
        "max_tokens": 500,
    }

def chat_benchmark_generator() -> dict:
    """Generate one benchmark payload for the /v1/chat/completions endpoint."""
    prompt = generate_random_text(200)
    
    model = os.environ.get("MODEL_NAME", "test-model")
    
    return {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 500,
    }

# --- Worker configuration -----------------------------------------------------

worker_config = WorkerConfig(
    model_server_url=MODEL_SERVER_URL,
    model_server_port=MODEL_SERVER_PORT,
    model_log_file=MODEL_LOG_FILE,

    handlers=[
        # /v1/completions: also used as the benchmark handler
        HandlerConfig(
            route="/v1/completions",
            
            # Allow parallel requests
            allow_parallel_requests=True,
            
            # Maximum time a request may sit in queue before being rejected
            max_queue_time=60.0,
            
            # Workload: use max_tokens as a simple cost proxy
            workload_calculator=lambda payload: float(payload.get("max_tokens", 0)),
            
            benchmark_config=BenchmarkConfig(
                # Use our generator to produce payloads
                generator=completions_benchmark_generator,
                runs=8,
                concurrency=10,
            ),
        ),
        
        # /v1/chat/completions: similar behavior but no benchmark_config
        HandlerConfig(
            route="/v1/chat/completions",
            allow_parallel_requests=True,
            max_queue_time=60.0,
            workload_calculator=lambda payload: float(payload.get("max_tokens", 0)),
        ),
        
        # /generate: simple generate endpoint
        HandlerConfig(
            route="/generate",
            allow_parallel_requests=True,
            max_queue_time=60.0,
            workload_calculator=lambda payload: 100.0,  # constant workload per request
        ),
    ],

    log_action_config=LogActionConfig(
        on_load=MODEL_LOAD_LOG_MSG,
        on_error=MODEL_ERROR_LOG_MSGS,
        on_info=MODEL_INFO_LOG_MSGS,
    ),
)

# Run the worker synchronously
if __name__ == "__main__":
    Worker(worker_config).run()
