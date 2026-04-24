import time


def run_llm(query, context):
    time.sleep(0.2)
    return f"LLM Answer to '{query}' using [{context}]"