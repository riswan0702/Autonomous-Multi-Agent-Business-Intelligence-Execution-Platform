"""
Memory Agent — ChromaDB-backed persistent vector store.

Implements ALL memory requirements:
  Conversation memory   — stores each agent's output per run (in-session)
  Persistent vector memory — ChromaDB on disk, survives restarts
  Retrieval system      — semantic similarity search
  Context recall        — injects relevant past runs into new workflow

Falls back gracefully if ChromaDB is not installed.
"""
import os
import hashlib
from datetime import datetime
from typing import Optional, List, Dict, Any


class MemoryStore:
    def __init__(self):
        memory_path = os.getenv("MEMORY_PATH", "./memory_store")
        os.makedirs(memory_path, exist_ok=True)
        self.enabled = False
        self.collection = None

        # Conversation memory — in-session, always available without ChromaDB
        # Structure: run_id → list of {agent, content, timestamp}
        self._conversation_memory: Dict[str, List[Dict]] = {}

        if os.getenv("ENABLE_MEMORY", "true").lower() != "true":
            print("[Memory] Disabled via config.")
            return

        # Try ChromaDB for persistent vector memory
        try:
            import chromadb
            from chromadb.config import Settings
            self.client = chromadb.PersistentClient(
                path=memory_path,
                settings=Settings(anonymized_telemetry=False),
            )
            self.collection = self.client.get_or_create_collection(
                name="bi_agent_memory",
                metadata={"description": "Business intelligence agent memory"},
            )
            self.enabled = True
            print(f"[Memory] ChromaDB ready at {memory_path}")
        except ImportError:
            print("[Memory] ChromaDB not installed — conversation memory active, vector memory disabled.")
        except Exception as e:
            print(f"[Memory] ChromaDB unavailable ({e}) — conversation memory active, vector memory disabled.")

    # ── CONVERSATION MEMORY ──────────────────────────────────────────────

    def add_to_conversation(self, run_id: str, agent_name: str, content: str):
        """Store agent output to in-session conversation memory."""
        if run_id not in self._conversation_memory:
            self._conversation_memory[run_id] = []
        self._conversation_memory[run_id].append({
            "agent": agent_name,
            "content": content[:2000],
            "timestamp": datetime.utcnow().isoformat(),
        })

    def get_conversation(self, run_id: str) -> List[Dict]:
        """Retrieve all agent outputs for a given run."""
        return self._conversation_memory.get(run_id, [])

    def get_conversation_summary(self, run_id: str) -> str:
        """Format conversation memory as context string."""
        messages = self.get_conversation(run_id)
        if not messages:
            return ""
        parts = ["### Conversation Memory (this session):"]
        for m in messages:
            parts.append(f"\n**{m['agent']}:** {m['content'][:300]}...")
        return "\n".join(parts)

    # ── PERSISTENT VECTOR MEMORY ─────────────────────────────────────────

    def store(self, run_id: str, agent_name: str, content: str, metadata: Optional[Dict] = None) -> bool:
        """Store to persistent ChromaDB vector store."""
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
        """Semantic similarity search over past runs."""
        if not self.enabled:
            return []
        try:
            count = self.collection.count()
            if count == 0:
                return []
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
        """Context recall — retrieve relevant past research for new workflow."""
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

        parts = ["### Relevant Past Research (context recall from memory):"]
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

    def get_stats(self) -> Dict:
        return {
            "vector_memory_enabled": self.enabled,
            "vector_memory_count": self.count(),
            "conversation_sessions": len(self._conversation_memory),
            "conversation_messages": sum(
                len(msgs) for msgs in self._conversation_memory.values()
            ),
        }


_memory_store: Optional[MemoryStore] = None


def get_memory_store() -> MemoryStore:
    global _memory_store
    if _memory_store is None:
        _memory_store = MemoryStore()
    return _memory_store
