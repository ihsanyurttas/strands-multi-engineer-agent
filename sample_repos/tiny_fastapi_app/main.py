"""
tiny_fastapi_app/main.py

Intentionally minimal FastAPI application used as a target for agent tasks.
It has several deliberate gaps (missing validation, no auth, etc.) that
the engineering agent will be asked to fix.
"""

from fastapi import FastAPI
from pydantic import BaseModel, Field


app = FastAPI(title="Tiny FastAPI App", version="0.1.0")


class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1)
    price: float = Field(..., gt=0)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/items")
def list_items():
    return {"items": []}


@app.post("/items")
def create_item(payload: ItemCreate):
    return {"created": payload.dict()}


@app.get("/items/{item_id}")
def get_item(item_id: int):
    return {"id": item_id, "name": "stub"}