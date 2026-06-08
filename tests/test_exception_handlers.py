import pytest
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from pydantic import BaseModel, ValidationError

from app.api.exception_handlers import (
    discover_domain_error_types,
    discover_mappings,
    validate_mappings,
)
from app.api.utils.response import (
    domain_error_to_response,
    pydantic_errors_to_details,
    unhandled_exception_to_response,
)
from app.core.exceptions.cart import CartNotFoundError, InvalidQuantityError
from app.core.exceptions.common import EntityNotFoundError


def test_discover_mappings_includes_cart_and_common_exceptions():
    mappings = discover_mappings()

    assert CartNotFoundError in mappings
    assert mappings[CartNotFoundError] == 404
    assert InvalidQuantityError in mappings
    assert mappings[InvalidQuantityError] == 400
    assert EntityNotFoundError in mappings
    assert mappings[EntityNotFoundError] == 404


def test_discover_domain_error_types_includes_all_concrete_subclasses():
    types = discover_domain_error_types()
    type_names = {exc_type.__name__ for exc_type in types}

    assert "CartNotFoundError" in type_names
    assert "InvalidQuantityError" in type_names
    assert "EntityNotFoundError" in type_names
    assert "InvalidOrderStateError" in type_names
    assert "DomainError" not in type_names


def test_validate_mappings_passes_when_all_types_are_mapped():
    mappings = discover_mappings()
    types = discover_domain_error_types()

    validate_mappings(mappings, types)


def test_validate_mappings_raises_when_mapping_is_missing():
    mappings = discover_mappings()
    types = discover_domain_error_types()
    incomplete_mappings = {
        exc_type: status_code
        for exc_type, status_code in mappings.items()
        if exc_type is not CartNotFoundError
    }

    with pytest.raises(RuntimeError, match="Missing HTTP mappings"):
        validate_mappings(incomplete_mappings, types)


def test_domain_error_to_response_uses_error_code_in_details():
    exc = CartNotFoundError("user123")
    response = domain_error_to_response(exc, 404)

    assert response.success is False
    assert response.code == 404
    assert response.message == "購物車 (user_id: user123) 不存在"
    assert response.errors is not None
    assert len(response.errors) == 1
    assert response.errors[0].message == exc.message
    assert response.errors[0].code == "CART_NOT_FOUND"


def test_pydantic_errors_to_details_skips_request_prefix():
    exc = RequestValidationError(
        [
            {
                "type": "missing",
                "loc": ("body", "email"),
                "msg": "Field required",
                "input": {},
            }
        ]
    )

    details = pydantic_errors_to_details(exc, skip_request_prefix=True)

    assert len(details) == 1
    assert details[0].field == "email"
    assert details[0].message == "Field required"
    assert details[0].code == "missing"


def test_pydantic_errors_to_details_uses_full_loc():
    class EmailModel(BaseModel):
        email: str

    try:
        EmailModel()
    except ValidationError as exc:
        details = pydantic_errors_to_details(exc, skip_request_prefix=False)
    else:
        pytest.fail("Expected ValidationError")

    assert len(details) == 1
    assert details[0].field == "email"
    assert details[0].code == "missing"


def test_unhandled_exception_to_response_hides_detail_when_debug_false(monkeypatch):
    monkeypatch.setenv("DEBUG", "false")

    response = unhandled_exception_to_response(RuntimeError("internal secret"))

    assert response.code == 500
    assert response.message == "伺服器內部錯誤"
    assert response.errors is None


def test_unhandled_exception_to_response_includes_detail_when_debug_true(monkeypatch):
    monkeypatch.setenv("DEBUG", "true")

    response = unhandled_exception_to_response(RuntimeError("internal secret"))

    assert response.code == 500
    assert response.message == "伺服器內部錯誤"
    assert response.errors is not None
    assert len(response.errors) == 1
    assert response.errors[0].message == "internal secret"


def test_domain_error_handler_returns_standard_error_response(client: TestClient):
    from dependency_injector import providers

    from app.api.routers import carts

    class StubCartService:
        def get_cart(self, user_id: str):
            raise CartNotFoundError(user_id)

    override = carts.container.services.cart_service.override(
        providers.Object(StubCartService())
    )
    with override:
        response = client.get("/api/cart?user_id=unknown")

    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["code"] == 404
    assert body["message"] == "購物車 (user_id: unknown) 不存在"
    assert body["errors"][0]["code"] == "CART_NOT_FOUND"


def test_invalid_quantity_returns_400_via_domain_error_handler(client: TestClient):
    from dependency_injector import providers

    from app.api.routers import carts

    class StubCartService:
        def add_item(self, user_id: str, product_id: str, unit_price: int, quantity: int = 1):
            raise InvalidQuantityError()

    override = carts.container.services.cart_service.override(
        providers.Object(StubCartService())
    )
    with override:
        response = client.post(
            "/api/cart/items?user_id=user123",
            json={"product_id": "prod456", "unit_price": 1000, "quantity": 1},
        )

    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert body["code"] == 400
    assert body["message"] == "quantity must be positive"
    assert body["errors"][0]["code"] == "INVALID_QUANTITY"
