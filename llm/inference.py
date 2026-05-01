import time
import random


def run_llm(query, context):
    """
    Simulates LLM inference processing with realistic latency.
    Represents GPU-accelerated inference with variable token generation times.
    Typically processes 50-200 tokens/second depending on batch size.
    """
    # Simulate variable inference time based on query complexity
    base_latency = 0.15  # Base inference latency in seconds
    query_complexity = len(query.split()) * 0.02  # ~20ms per word
    random_variance = random.uniform(0.0, 0.1)  # Add variance for realism
    
    total_latency = base_latency + query_complexity + random_variance
    time.sleep(total_latency)
    
    # Simulate realistic LLM output
    model_name = "GPT-like-model"
    return f"LLM ({model_name}) Answer to '{query}' using context: [{context}]"