from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import configs, results, auth, jobs, metrics

app = FastAPI(
    title="Universal Web Scraper & Gemini Enrichment Platform",
    description="Config-driven, resilient scraper with Gemini AI enrichment",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(configs.router, prefix="/api/configs", tags=["scrape-configs"])
app.include_router(results.router, prefix="/api/results", tags=["scrape-results"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["scrape-jobs"])
app.include_router(metrics.router, prefix="/api/metrics", tags=["metrics"])


@app.get("/")
def root():
    return {"message": "Universal Web Scraper & Gemini Enrichment Platform API"}


@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "0.1.0"}