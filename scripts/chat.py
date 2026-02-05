import os
from dotenv import load_dotenv

from rag_system.config import load_settings
from rag_system.embeddings.dense import DenseEmbedder
from rag_system.retrieval.router import RetrievalRouter
from rag_system.prompting.prompt_builder import PromptBuilder
from rag_system.llm.gemini_gemma import GemmaClient
from rag_system.app.pipeline import RAGPipeline

VALID_MODES = {"fixed", "semantic", "auto"}  # Remove "both"

def ask_mode(default_mode: str) -> str:
    m = input(f"Choose chunking mode [{default_mode}] (fixed/semantic/auto): ").strip().lower()
    if not m:
        return default_mode
    if m not in VALID_MODES:
        print("Invalid mode. Using default:", default_mode)
        return default_mode
    return m

def main():
    load_dotenv()
    s = load_settings()

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Missing GEMINI_API_KEY in .env")

    # 1) Build shared components
    embedder = DenseEmbedder(s.embed_model, normalize=s.normalize_embeddings)
    router = RetrievalRouter(artifacts_root=s.artifacts_dir, embedder=embedder, ef_search=s.ef_search)
    prompt_builder = PromptBuilder(s.prompts_dir)
    llm = GemmaClient(api_key=api_key, model=s.llm_model)

    pipeline = RAGPipeline(router=router, prompt_builder=prompt_builder, llm=llm, settings=s)

    # 2) Choose mode
    mode = ask_mode(s.chunking_mode_default)

    print("\n Hybrid RAG Chat Ready")
    print("Commands:")
    print("  /mode fixed|semantic|auto   -> switch search mode")
    print("  /exit                           -> quit")

    while True:
        q = input("\nQ: ").strip()
        if not q:
            continue
        if q.lower() in ("/exit", "exit", "quit"):
            break

        if q.lower().startswith("/mode"):
            parts = q.split()
            if len(parts) == 2 and parts[1].lower() in VALID_MODES:
                mode = parts[1].lower()
                print("Mode switched to:", mode)
            else:
                print("Usage: /mode fixed|semantic|auto")
            continue

        result = pipeline.answer(q, mode=mode)

        print("\nA:\n", result.answer)

        # Optional small explainability
        print("\nTop sources:")
        for r in result.retrieved[: min(5, len(result.retrieved))]:
            print(f" - {r.get('chunk_id')} | strategy={r.get('strategy')} | bm25={r.get('bm25_rank')} | dense={r.get('dense_rank')}")

if __name__ == "__main__":
    main()
