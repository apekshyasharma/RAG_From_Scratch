from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv

from webapp.app.routes.pages import router as pages_router
from webapp.app.routes.api_chat import router as api_router
from webapp.app.settings import WebSettings

# Import RAG objects 
from rag_system.config import load_settings
from rag_system.embeddings.dense import DenseEmbedder
from rag_system.retrieval.router import RetrievalRouter
from rag_system.prompting.prompt_builder import PromptBuilder
from rag_system.llm.gemini_gemma import GemmaClient
from rag_system.app.pipeline import RAGPipeline


def create_app() -> FastAPI:
    app = FastAPI(title="RAG Chatbot", version="0.1.0")

    app.mount("/static", StaticFiles(directory="webapp/app/static"), name="static")
    app.include_router(pages_router)
    app.include_router(api_router)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.on_event("startup")
    async def startup():
        load_dotenv()
        
        # Load settings via existing config system
        settings = load_settings()

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Missing GEMINI_API_KEY in .env")

        # Initialize components with correct signatures
        embedder = DenseEmbedder(settings.embed_model, normalize=settings.normalize_embeddings)
        router = RetrievalRouter(
            artifacts_root=settings.artifacts_dir,
            embedder=embedder,
            ef_search=settings.ef_search
        )
        pb = PromptBuilder(prompts_dir=settings.prompts_dir)
        llm = GemmaClient(api_key=api_key, model=settings.llm_model)

        app.state.settings = settings
        app.state.rag_pipeline = RAGPipeline(router=router, prompt_builder=pb, llm=llm, settings=settings)

    return app


app = create_app()
