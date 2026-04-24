KNOWLEDGE_BASE = {
    "distributed": "Distributed systems coordinate multiple nodes to handle scale and reliability.",
    "load balancing": "Load balancing distributes incoming work across workers to avoid hotspots.",
    "gpu": "GPU workers accelerate matrix-heavy inference for LLM serving.",
    "rag": "RAG injects retrieved context into prompts to improve factual grounding.",
    "fault tolerance": "Fault tolerance keeps service running by detecting failures and rerouting work.",
    "llm": "LLMs generate language responses conditioned on prompts and context.",
}


def retrieve_context(query):
    lowered = query.lower()
    matches = [text for keyword, text in KNOWLEDGE_BASE.items() if keyword in lowered]

    if matches:
        return " | ".join(matches)

    return (
        "General distributed AI context: process requests with retrieval, "
        "balanced scheduling, and resilient worker execution."
    )