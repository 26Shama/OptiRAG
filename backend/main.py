from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# NLP initializer
from .pipeline.nlp_init import initialize_nlp

# Routers
from .routers.auth import router as auth_router
from .routers.health import router as health_router
from .routers.upload import resumes_router, jd_router
from .routers.matching import router as matching_router
from .routers.reports import router as reports_router
from .routers.training import router as training_router
from .routers.hr_emailer import router as hr_emailer_router

# ✅ CHATBOT ADDITION (IMPORT)
from .routers.chat import router as chat_router
from dotenv import load_dotenv
load_dotenv()


initialize_nlp()

def create_app() -> FastAPI:
    """
    Factory function to build FastAPI app.
    Central entry point for backend.
    """
    app = FastAPI(
        title="OptiRAG Backend",
        description="FastAPI Backend for Resume Ranking & HR Automation",
        version="1.0.0",
    )

    # -----------------------------
    # CORS Settings (for frontend)
    # -----------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # -----------------------------
    # Startup: Load NLP
    # -----------------------------
    @app.on_event("startup")
    def startup_event():
        print("🔁 Initializing spaCy NLP + Skill Matcher...")
        initialize_nlp()
        print("✅ NLP & Skills Ready")

    # -----------------------------
    # Register Routers
    # -----------------------------
    app.include_router(health_router, prefix="/health", tags=["Health Check"])

    # Auth first
    app.include_router(auth_router, prefix="/auth", tags=["Authentication"])

    # Upload resumes & JD
    app.include_router(resumes_router, prefix="/resumes", tags=["Resumes Upload"])
    app.include_router(jd_router, prefix="/jd", tags=["JD Upload"])

    # Resume ranking
    app.include_router(matching_router, prefix="/matching", tags=["Matching & Ranking"])

    # Reports
    app.include_router(reports_router, prefix="/reports", tags=["Reports & Output"])

    # Training
    app.include_router(training_router, prefix="/train", tags=["Continuous Learning"])

    # HR Emailer
    app.include_router(
        hr_emailer_router,
        prefix="/api/hr-emailer",
        tags=["HR Emailer"]
    )

    # ✅ CHATBOT ADDITION (REGISTER ROUTER)
    app.include_router(
        chat_router,
        prefix="/chat",
        tags=["Chatbot"]
    )

    return app


app = create_app()
