import json
import pickle
from pathlib import Path
import numpy as np

from rag_system.config import load_settings
from rag_system.ingestion.pdf_loader import extract_text_from_pdf
from rag_system.chunking.build_chunks import build_chunks_for_doc
from rag_system.embeddings.dense import DenseEmbedder
from rag_system.embeddings.sparse import build_bm25
from rag_system.vectorstore.faiss_hnsw import FaissHNSW
from rag_system.vectorstore.persistence import save_jsonl

def build_one_index(mode: str, chunks: list, vecs: np.ndarray, artifacts_root: Path, s):
    """
    Saves artifacts to:
      artifacts/<mode>/
        chunks.jsonl
        dense_embeddings.npy
        faiss_hnsw.index
        bm25.pkl
        metadata.json
    """
    out_dir = artifacts_root / mode
    out_dir.mkdir(parents=True, exist_ok=True)

    # chunks
    save_jsonl(out_dir / "chunks.jsonl", chunks)

    # embeddings
    np.save(out_dir / "dense_embeddings.npy", vecs)

    # FAISS HNSW
    store = FaissHNSW(dim=vecs.shape[1], M=s.hnsw_M, ef_construction=s.ef_construction, ef_search=s.ef_search)
    store.add(vecs)
    store.save(str(out_dir / "faiss_hnsw.index"))

    # BM25
    bm25 = build_bm25(chunks)
    with open(out_dir / "bm25.pkl", "wb") as f:
        pickle.dump(bm25, f)

    # meta
    meta = {
        "mode": mode,
        "chunk_count": len(chunks),
        "embed_model": s.embed_model,
        "normalize_embeddings": s.normalize_embeddings,
        "chunk_size": s.chunk_size,
        "overlap": s.overlap,
        "faiss": {"type": "hnsw", "M": s.hnsw_M, "efConstruction": s.ef_construction, "efSearch": s.ef_search},
    }
    (out_dir / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

def main():
    s = load_settings()
    s.artifacts_dir.mkdir(parents=True, exist_ok=True)

    pdfs = sorted(s.pdf_dir.glob("*.pdf"))
    if not pdfs:
        raise FileNotFoundError(f"No PDFs found in: {s.pdf_dir.resolve()}")

    embedder = DenseEmbedder(s.embed_model, normalize=s.normalize_embeddings)

    fixed_chunks_all = []
    semantic_chunks_all = []

    # 1) Ingest + chunk into two corpora
    for pdf in pdfs:
        raw = extract_text_from_pdf(pdf)
        built = build_chunks_for_doc(
            source_path=pdf,
            text=raw,
            chunk_size=s.chunk_size,
            overlap=s.overlap,
            fixed_enabled=s.fixed_enabled,
            semantic_enabled=s.semantic_enabled
        )
        fixed_chunks_all.extend(built["fixed"])
        semantic_chunks_all.extend(built["semantic"])

    # 2) Dense embeddings for each corpus
    if s.fixed_enabled:
        fixed_vecs = embedder.encode([c["text"] for c in fixed_chunks_all])
        build_one_index("fixed", fixed_chunks_all, fixed_vecs, s.artifacts_dir, s)

    if s.semantic_enabled:
        sem_vecs = embedder.encode([c["text"] for c in semantic_chunks_all])
        build_one_index("semantic", semantic_chunks_all, sem_vecs, s.artifacts_dir, s)

    print("Index build complete")
    print("Artifacts directory:", s.artifacts_dir.resolve())
    if s.fixed_enabled:
        print(" - fixed:", len(fixed_chunks_all), "chunks")
    if s.semantic_enabled:
        print(" - semantic:", len(semantic_chunks_all), "chunks")

if __name__ == "__main__":
    main()
