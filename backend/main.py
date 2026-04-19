from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import providers, fhir, chatbot

app = FastAPI(title="Healthcare Burden Navigator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(providers.router, prefix="/api/v1")
app.include_router(fhir.router, prefix="/api/v1")
app.include_router(chatbot.router, prefix="/api/v1")


@app.get("/")
def root():
    return {"status": "ok", "message": "Healthcare Burden Navigator API"}
