"""
tiny_fastapi_app/main.py

Intentionally minimal FastAPI application used as a target for agent tasks.
It has several deliberate gaps (missing validation, no auth, etc.) that
the engineering agent will be asked to fix.
"""

from fastapi import FastAPI

app = FastAPI(title="Tiny FastAPI App", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/items")
def list_items():
    # TODO: replace with a real data store
    return {"items": []}


@app.post("/items")
def create_item(payload: dict):
    # No validation — accepts any dict.
    # Agent task: add Pydantic model validation.
    return {"created": payload}


@app.get("/items/{item_id}")
def get_item(item_id: int):
    # No 404 handling — always returns a stub.
    return {"id": item_id, "name": "stub"}
