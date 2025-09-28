''' Authored by Akshata Madavi '''

from fastapi import FastAPI

from src.routes import issues

app = FastAPI()

@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/")
def read_root():
    return {"Hello": "World"}

app.include_router(issues.router, prefix="/issues", tags=["issues"])