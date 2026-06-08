from fastapi import APIRouter
from fastapi.testclient import TestClient

from app.api.router_discovery import discover_routers
from app.api.routers import carts
from app.application.app import create_app


def test_discover_routers_includes_carts_router():
    routers = discover_routers()
    assert carts.router in routers


def test_discover_routers_returns_only_api_routers():
    routers = discover_routers()
    assert routers
    assert all(isinstance(router, APIRouter) for router in routers)


def test_create_app_exposes_cart_endpoints_in_openapi(client: TestClient):
    response = client.get("/openapi.json")
    assert response.status_code == 200

    paths = response.json()["paths"]
    assert "/api/cart" in paths
    assert "/api/cart/items" in paths


def test_create_app_registers_routers_without_manual_include():
    app = create_app(init_db=False)
    with TestClient(app) as test_client:
        response = test_client.get("/openapi.json")
        assert response.status_code == 200
        assert "/api/cart" in response.json()["paths"]
