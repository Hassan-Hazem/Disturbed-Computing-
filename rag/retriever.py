import random


KNOWLEDGE_BASE = {
    "distributed": "Distributed systems coordinate multiple nodes to handle scale and reliability.",
    "load balancing": "Load balancing distributes incoming work across workers to avoid hotspots.",
    "gpu": "GPU workers accelerate matrix-heavy inference for LLM serving.",
    "rag": "RAG injects retrieved context into prompts to improve factual grounding.",
    "fault tolerance": "Fault tolerance keeps service running by detecting failures and rerouting work.",
    "llm": "LLMs generate language responses conditioned on prompts and context.",
    "inference": "Inference involves running trained models to generate predictions.",
    "scaling": "Scaling systems requires handling increasing load through parallelization.",
    "latency": "Latency measures response time from request to completion.",
    "throughput": "Throughput measures the number of requests processed per second.",
    "concurrency": "Concurrency allows multiple requests to be processed simultaneously.",
    "clustering": "Clustering groups similar data points together for organization.",
    "optimization": "Optimization improves system performance through tuning parameters.",
    "monitoring": "Monitoring tracks system health and performance metrics in real-time.",
    "scheduling": "Scheduling allocates tasks to available resources efficiently.",
    "resilience": "Resilience enables systems to recover from failures automatically.",
    "resource utilization": "Resource utilization measures how efficiently hardware is used.",
    "request handling": "Request handling processes incoming client demands efficiently.",
    "task distribution": "Task distribution spreads work across multiple worker nodes.",
    "performance metrics": "Performance metrics quantify system behavior and effectiveness.",
}


def retrieve_context(query):
    """
    Retrieves relevant context from knowledge base using keyword matching.
    Simulates a vector database or semantic search by matching keywords.
    Returns up to 3 most relevant contexts from the knowledge base.
    """
    lowered = query.lower()
    
    # Find all matching contexts
    matches = []
    for keyword, context_text in KNOWLEDGE_BASE.items():
        if keyword in lowered:
            matches.append(context_text)
    
    # If we have matches, return up to 3 most relevant ones
    if matches:
        # Return first 3 matches, or fewer if not available
        selected = matches[:3]
        return " | ".join(selected)
    
    # Default fallback context
    default_contexts = [
        "Distributed systems handle large-scale data processing and service reliability.",
        "Load balancing optimizes resource usage across multiple servers.",
        "GPU acceleration enables fast LLM inference for production systems.",
        "RAG systems enhance LLM responses with real-time knowledge retrieval.",
        "Fault tolerance mechanisms ensure continuous service availability.",
    ]
    
    return random.choice(default_contexts)