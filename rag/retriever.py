"""
RAG retrieval module with embeddings and top-k search.

FAISS is used automatically when installed. The standard-library fallback uses
the same normalized hashed embeddings and cosine search, so the project remains
runnable in a clean classroom Python environment.
"""

import asyncio
import hashlib
import math
import re
from dataclasses import dataclass
from typing import List, Sequence, Tuple

import config

try:
    import faiss  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    faiss = None


TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9_]+")


@dataclass(frozen=True)
class Document:
    title: str
    text: str


SAMPLE_DATASET: Sequence[Document] = (
    Document(
        "Distributed scheduling",
        "A master node tracks worker health, queue pressure, and task state before assigning requests to available workers.",
    ),
    Document(
        "Round robin load balancing",
        "Round robin distributes requests cyclically. It is simple and fair when workers have similar hardware and request costs.",
    ),
    Document(
        "Least connections load balancing",
        "Least connections routes each request to the worker with the fewest active requests, improving behavior for uneven workloads.",
    ),
    Document(
        "Load-aware routing",
        "Load-aware routing combines active connections, average latency, utilization, and recent failures to avoid overloaded or unhealthy workers.",
    ),
    Document(
        "GPU inference",
        "GPU workers accelerate LLM inference by batching tensor operations and running several requests concurrently up to memory limits.",
    ),
    Document(
        "RAG",
        "Retrieval augmented generation embeds the user query, retrieves top-k relevant documents, and injects that context into the LLM prompt.",
    ),
    Document(
        "Fault tolerance",
        "Fault-tolerant systems detect failed workers, stop routing new tasks to them, and reassign in-flight tasks to healthy replicas.",
    ),
    Document(
        "No request loss",
        "A scheduler can preserve request state and retry failed tasks so client requests are either completed or reported after bounded retries.",
    ),
    Document(
        "Throughput",
        "Throughput measures completed requests per second and increases when work is parallelized across more healthy workers.",
    ),
    Document(
        "Latency",
        "Latency is the end-to-end response time observed by a request, including scheduling, retrieval, LLM inference, and retry delay.",
    ),
    Document(
        "Worker utilization",
        "Worker utilization compares active connections with worker concurrency capacity and helps the load balancer avoid hot spots.",
    ),
    Document(
        "LLM provider retries",
        "Production LLM API calls require timeout handling, retries, and latency logging because remote providers can throttle or fail transiently.",
    ),
)


def _tokens(text: str) -> List[str]:
    return [token.lower() for token in TOKEN_PATTERN.findall(text)]


def embed_text(text: str, dimensions: int = None) -> List[float]:
    """Create a normalized hashing-vector embedding for a text string."""
    dimensions = dimensions or config.EMBEDDING_DIMENSIONS
    vector = [0.0] * dimensions

    for token in _tokens(text):
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


class VectorRetriever:
    def __init__(self, documents: Sequence[Document]):
        self.documents = list(documents)
        self.embeddings = [embed_text(f"{doc.title} {doc.text}") for doc in self.documents]
        self.index = None

        if faiss is not None and self.embeddings:
            try:
                import numpy as np  # type: ignore

                matrix = np.array(self.embeddings, dtype="float32")
                self.index = faiss.IndexFlatIP(matrix.shape[1])
                self.index.add(matrix)
            except Exception:
                self.index = None

    def search(self, query: str, top_k: int = None) -> List[Tuple[Document, float]]:
        top_k = top_k or config.RAG_TOP_K
        query_embedding = embed_text(query)

        if self.index is not None:
            import numpy as np  # type: ignore

            query_matrix = np.array([query_embedding], dtype="float32")
            scores, indexes = self.index.search(query_matrix, min(top_k, len(self.documents)))
            return [
                (self.documents[int(index)], float(score))
                for score, index in zip(scores[0], indexes[0])
                if int(index) >= 0
            ]

        scored = [
            (document, _cosine(query_embedding, embedding))
            for document, embedding in zip(self.documents, self.embeddings)
        ]
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:top_k]


_retriever = VectorRetriever(SAMPLE_DATASET)


def retrieve_documents(query: str, top_k: int = None) -> List[Tuple[Document, float]]:
    return _retriever.search(query, top_k=top_k)


def retrieve_context(query: str, top_k: int = None) -> str:
    matches = retrieve_documents(query, top_k=top_k)
    return "\n".join(
        f"[{document.title} | score={score:.3f}] {document.text}"
        for document, score in matches
    )


async def retrieve_context_async(query: str, top_k: int = None) -> str:
    return await asyncio.to_thread(retrieve_context, query, top_k)
