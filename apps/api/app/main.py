from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import prompts, criteria, evals

app = FastAPI(title="Sparkling Prompt Studio API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://172.30.10.242:3000",  
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True}

app.include_router(prompts.router)
app.include_router(criteria.router)
app.include_router(evals.router)