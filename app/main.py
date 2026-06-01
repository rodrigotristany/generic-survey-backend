from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import admin_auth, admin_surveys, public_surveys, responses, user_auth

app = FastAPI(
    title="Generic Survey API",
    version="1.0.0",
    description="API for creating and responding to surveys.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin_auth.router)
app.include_router(user_auth.router)
app.include_router(admin_surveys.router)
app.include_router(public_surveys.router)
app.include_router(responses.router)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}
