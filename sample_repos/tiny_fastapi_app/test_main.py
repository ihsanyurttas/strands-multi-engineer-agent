"""
tiny_fastapi_app/test_main.py

Unit tests for the POST /items endpoint, covering:
  - Valid payload  → HTTP 200 with echoed data
  - Invalid payloads → HTTP 422 Unprocessable Entity
"""

import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_create_item_valid(client):
    response = client.post("/items", json={"name": "Widget", "price": 9.99})
    assert response.status_code == 200
    assert response.json() == {"created": {"name": "Widget", "price": 9.99}}


@pytest.mark.parametrize("payload,description", [
    ({}, "both fields missing"),
    ({"price": 9.99}, "name field missing"),
    ({"name": "Widget"}, "price field missing"),
    ({"name": "", "price": 9.99}, "name is empty string"),
    ({"name": "Widget", "price": 0}, "price is zero (not > 0)"),
    ({"name": "Widget", "price": -1.0}, "price is negative"),
    ({"name": "Widget", "price": "free"}, "price is a non-numeric string"),
])
def test_create_item_invalid(client, payload, description):
    response = client.post("/items", json=payload)
    assert response.status_code == 422, (
        f"Expected 422 for case '{description}', "
        f"got {response.status_code}. Body: {response.text}"
    )