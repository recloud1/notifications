from endpoints.core.constants import ApiRoutes, RequestMethods
from endpoints.core.types import RequestResult
from starlette.testclient import TestClient

from core.config import envs


async def api_request(
    request_client: TestClient,
    method: RequestMethods,
    route: ApiRoutes,
    route_detail: str = "",
    query_params: dict | None = None,
    data: dict | None = None,
    headers: dict | None = None,
    # with_check: bool = True,
) -> RequestResult:
    if not headers:
        headers = {}

    headers.update({"Authorization": "Bearer test_token"})
    response = request_client.request(
        method=method,
        url=f"http://{envs.app.host}:{envs.app.port}/{route}{route_detail}",
        params=query_params,
        json=data,
        headers=headers,
    )

    # if with_check:
    #     assert response.status_code == HTTPStatus.OK, response

    data = response.json()

    return response, data
