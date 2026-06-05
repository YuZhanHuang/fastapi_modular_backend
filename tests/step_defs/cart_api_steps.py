from dependency_injector import providers
from pytest_bdd import given, parsers, scenarios, then, when

from tests.support.context import ScenarioContext

scenarios("../features/api/cart_api.feature")


def _response_body(context: ScenarioContext) -> dict:
    body = context.response.json()
    if isinstance(body.get("detail"), dict):
        return body["detail"]
    return body


@given("API 應用已啟動")
def api_ready(context: ScenarioContext, client, container) -> None:
    context.client = client
    context.container = container


@given("購物車服務回傳空結果")
def stub_empty_cart(context: ScenarioContext, container) -> None:
    class StubCartService:
        def get_cart(self, user_id: str):
            return None

    override = container.services.cart_service.override(
        providers.Object(StubCartService())
    )
    override.__enter__()
    context.add_cleanup(override.__exit__, None, None, None)


@when(parsers.parse('客戶端請求 "{method}" "{path}"'))
def http_request(context: ScenarioContext, method: str, path: str) -> None:
    context.response = context.client.request(method, path)


@then(parsers.parse("回應狀態碼應為 {status:d}"))
def assert_status(context: ScenarioContext, status: int) -> None:
    assert context.response.status_code == status


@then(parsers.parse('回應欄位 "{field}" 應為 {expected}'))
def assert_response_field(context: ScenarioContext, field: str, expected: str) -> None:
    body = _response_body(context)
    actual = body[field]

    if expected == "false":
        assert actual is False
    elif expected == "true":
        assert actual is True
    elif expected.isdigit():
        assert actual == int(expected)
    else:
        assert str(actual) == expected
