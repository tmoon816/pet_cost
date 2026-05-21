from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.v1 import categories, costs, customers, pets, stats
from .core.config import settings
from .core.exceptions import ConflictError

app = FastAPI(title="Pet Cost API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ConflictError)
async def conflict_handler(request: Request, exc: ConflictError):
    return JSONResponse(status_code=409, content={"detail": exc.detail})


@app.get("/")
def root():
    return {"name": "pet-cost", "version": "0.1.0"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


for module in (customers, pets, costs, categories, stats):
    app.include_router(module.router, prefix="/api/v1")
