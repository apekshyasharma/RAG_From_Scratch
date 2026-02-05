from dataclasses import dataclass
from pathlib import Path
import pickle

from rag_system.vectorstore.persistence import load_jsonl
from rag_system.vectorstore.faiss_hnsw import FaissHNSW
from rag_system.embeddings.sparse import bm25_tokenize
from rag_system.embeddings.dense import DenseEmbedder
from rag_system.retrieval.hybrid import hybrid_retrieve  # Keep this, remove rrf_fuse import

@dataclass
class RetrievalAssets:
    chunks: list
    bm25: object
    faiss: FaissHNSW


class RetrievalRouter:
    """
    Loads retrieval assets for fixed/semantic indexes and routes queries
    based on user-selected mode: fixed | semantic | auto
    """
    def __init__(self, artifacts_root: Path, embedder: DenseEmbedder, ef_search: int):
        self.root = artifacts_root
        self.embedder = embedder
        self.ef_search = ef_search
        self._cache = {}  # mode -> RetrievalAssets

    def _load_mode(self, mode: str) -> RetrievalAssets:
        if mode in self._cache:
            return self._cache[mode]

        mode_dir = self.root / mode
        chunks = load_jsonl(mode_dir / "chunks.jsonl")

        with open(mode_dir / "bm25.pkl", "rb") as f:
            bm25 = pickle.load(f)

        faiss_store = FaissHNSW.load(str(mode_dir / "faiss_hnsw.index"), ef_search=self.ef_search)

        assets = RetrievalAssets(chunks=chunks, bm25=bm25, faiss=faiss_store)
        self._cache[mode] = assets
        return assets

    def _auto_mode(self, query: str) -> str:
        """
        Simple heuristic:
        - if query contains lots of symbols/digits/short tokens => fixed
        - else => semantic
        """
        q = query.strip()
        score_fixed = sum(ch.isdigit() for ch in q) + sum(ch in "[](){}=+-*/_^" for ch in q)
        if score_fixed >= 2 or len(q.split()) <= 5:
            return "fixed"
        return "semantic"

    def retrieve(self, query: str, mode: str, bm25_k: int, dense_k: int, final_k: int, rrf_k: int, max_per_doc: int):
        mode = mode.lower().strip()
        
        if mode == "auto":
            mode = self._auto_mode(query)

        if mode not in ("fixed", "semantic"):
            raise ValueError(f"Invalid mode: {mode}. Use 'fixed', 'semantic', or 'auto'.")

        a = self._load_mode(mode)
        return hybrid_retrieve(
            query=query,
            chunks=a.chunks,
            bm25=a.bm25,
            tokenize_fn=bm25_tokenize,
            embedder=self.embedder,
            faiss_store=a.faiss,
            bm25_k=bm25_k,
            dense_k=dense_k,
            final_k=final_k,
            rrf_k=rrf_k,  
            max_per_doc=max_per_doc
        )
