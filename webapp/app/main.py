from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from webapp.app.routes.pages import router as pages_router

def create_app() -> FastAPI:
    app = FastAPI(
        title="RAG Chatbot",
        description="""A chatbot that uses Retrieval-Augmented Generation (RAG) to provide accurate and relevant responses based on classical ML and AI research papers.""",
        version="1.0.0"
    )
    # Middleware to serve CSS and JS files
    app.mount("/static", StaticFiles(directory="webapp/app/static"), name="static")
    # Include the Jinja2 template routes
    app.include_router(pages_router)
    return app

app = create_app()


