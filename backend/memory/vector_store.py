"""
Memory Agent — ChromaDB-backed persistent vector store.
Stores agent outputs per run and retrieves relevant context for future runs.
Falls back gracefully if ChromaDB is unavailable.
"""
import os
import hashlib
from datetime import datetime
from typing import Optional, List, Dict, Any
import chromadb
from chromadb.config import Settings


class MemoryStore:
    def __init__(self):
        memory_path = os.getenv("MEMORY_PATH", "./memory_store")
        os.makedirs(memory_path, exist_ok=True)
        self.enabled = os.getenv("ENABLE_MEMORY", "true").lower() == "true"

        if self.enabled:
            try:
                self.client = chromadb.PersistentClient(
                    path=memory_path,
                    settings=Settings(anonymized_telemetry=False),
                )
                self.collection = self.client.get_or_create_collection(
                    name="bi_agent_memory",
                    metadata={"description": "Business intelligence agent memory"},
                )
                print(f"[Memory] ChromaDB ready at {memory_path}")
            except Exception as e:
                print(f"[Memory] ChromaDB init failed ({e}). Running without memory.")
                self.enabled = False

    def store(self, run_id: str, agent_name: str, content: str, metadata: Optional[Dict] = None) -> bool:
        if not self.enabled or not content.strip():
            return False
        try:
            doc_id = f"{run_id}:{agent_name}:{hashlib.md5(content.encode()).hexdigest()[:8]}"
            meta = {
                "run_id": run_id,
                "agent": agent_name,
                "timestamp": datetime.utcnow().isoformat(),
                **(metadata or {}),
            }
            self.collection.add(
                documents=[content[:8000]],
                metadatas=[meta],
                ids=[doc_id],
            )
            return True
        except Exception as e:
            print(f"[Memory] Store error: {e}")
            return False

    def retrieve(self, query: str, n_results: int = 3, agent_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self.enabled:
            return []
        try:
            count = self.collection.count()
            if count == 0:
                return []
            # FIX: never request more results than documents that exist
            actual_n = max(1, min(n_results, count))
            where = {"agent": agent_filter} if agent_filter else None
            results = self.collection.query(
                query_texts=[query],
                n_results=actual_n,
                where=where,
            )
            memories = []
            for i, doc in enumerate(results["documents"][0]):
                memories.append({
                    "content": doc,
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i] if results.get("distances") else None,
                })
            return memories
        except Exception as e:
            print(f"[Memory] Retrieve error: {e}")
            return []

    def get_context_for_run(self, business_input: Dict) -> str:
        if not self.enabled:
            return ""
        try:
            if self.collection.count() == 0:
                return ""
        except Exception:
            return ""

        query = " ".join([
            business_input.get("company", ""),
            business_input.get("product", ""),
            business_input.get("target_audience", ""),
        ])
        memories = self.retrieve(query, n_results=3)
        if not memories:
            return ""

        parts = ["### Relevant Past Research (from memory):"]
        for m in memories:
            agent = m["metadata"].get("agent", "unknown")
            ts = m["metadata"].get("timestamp", "")[:10]
            parts.append(f"\n**{agent}** ({ts}):\n{m['content'][:400]}...")
        return "\n".join(parts)

    def count(self) -> int:
        if not self.enabled:
            return 0
        try:
            return self.collection.count()
        except Exception:
            return 0


_memory_store: Optional[MemoryStore] = None


def get_memory_store() -> MemoryStore:
    global _memory_store
    if _memory_store is None:
        _memory_store = MemoryStore()
    return _memory_store
