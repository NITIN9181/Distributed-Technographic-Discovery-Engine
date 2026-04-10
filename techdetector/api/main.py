"""
TechDetector REST API

OpenAPI docs at /docs
ReDoc at /redoc
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from .routes import companies, technologies, search, webhooks, exports
from .middleware.rate_limit import RateLimitMiddleware
from .middleware.tenant import TenantMiddleware
from .auth.api_keys import verify_api_key

app = FastAPI(
    title="TechDetector API",
    description="Technographic intelligence at scale",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure per environment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# We will use simple dependencies instead of middleware for rate limiting and tenant settings if needed
# app.add_middleware(RateLimitMiddleware)
# app.add_middleware(TenantMiddleware)

app.include_router(companies.router, prefix="/api/v1", tags=["Companies"])
app.include_router(technologies.router, prefix="/api/v1", tags=["Technologies"])
app.include_router(search.router, prefix="/api/v1", tags=["Search"])
app.include_router(webhooks.router, prefix="/api/v1", tags=["Webhooks"])
app.include_router(exports.router, prefix="/api/v1", tags=["Exports"])

@app.get("/health")
async def health():
    return {"status": "healthy"}
