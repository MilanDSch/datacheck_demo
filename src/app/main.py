from fastapi import FastAPI

from .routers import datasets

app = FastAPI(title="DataCheck API")
app.include_router(datasets.router, prefix="/api/v1")
