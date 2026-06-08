from pytest_bdd import given, parsers, scenarios, then, when

from app.core.exceptions.base import DomainError
from app.core.exceptions.cart import InvalidQuantityError
from app.core.services.cart_service import CartService
from tests.support.context import ScenarioContext
from tests.support.fakes.fake_cart_repository import FakeCartRepository

scenarios("../features/cart/add_item.feature")
scenarios("../features/cart/get_cart.feature")


@given("購物車服務使用空的儲存庫")
def cart_service_with_empty_repo(context: ScenarioContext) -> None:
    context.repo = FakeCartRepository()
    context.service = CartService(cart_repo=context.repo)


@when(parsers.parse('使用者 "{user_id}" 加入商品 "{product_id}" 數量 {quantity:d} 單價 {unit_price:d}'))
def add_item(
    context: ScenarioContext,
    user_id: str,
    product_id: str,
    quantity: int,
    unit_price: int,
) -> None:
    context.exception = None
    context.result = context.service.add_item(
        user_id=user_id,
        product_id=product_id,
        unit_price=unit_price,
        quantity=quantity,
    )


@when(
    parsers.parse(
        '使用者 "{user_id}" 嘗試加入商品 "{product_id}" 數量 {quantity:d} 單價 {unit_price:d}'
    )
)
def add_item_expecting_error(
    context: ScenarioContext,
    user_id: str,
    product_id: str,
    quantity: int,
    unit_price: int,
) -> None:
    context.exception = None
    try:
        context.service.add_item(
            user_id=user_id,
            product_id=product_id,
            unit_price=unit_price,
            quantity=quantity,
        )
    except DomainError as exc:
        context.exception = exc


@when(parsers.parse('使用者 "{user_id}" 取得購物車'))
def get_cart(context: ScenarioContext, user_id: str) -> None:
    context.result = context.service.get_cart(user_id)


@then(parsers.parse("購物車總金額應為 {expected:d}"))
def assert_total(context: ScenarioContext, expected: int) -> None:
    assert context.result.total_amount() == expected


@then(parsers.parse("購物車應有 {count:d} 個項目"))
def assert_item_count(context: ScenarioContext, count: int) -> None:
    assert len(context.result.items) == count


@then("應拋出 InvalidQuantityError")
def assert_invalid_quantity_error(context: ScenarioContext) -> None:
    assert isinstance(context.exception, InvalidQuantityError)
