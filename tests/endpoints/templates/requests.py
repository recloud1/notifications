from uuid import uuid4

from endpoints.core.constants import ApiRoutes, RequestMethods
from endpoints.core.types import RequestResult
from endpoints.utils.requests import api_request
from starlette.testclient import TestClient


async def get_templates(client: TestClient, with_check: bool = True) -> RequestResult:
    response, data = await api_request(
        client,
        RequestMethods.get,
        ApiRoutes.templates,
    )

    return response, data


async def get_template(
    client: TestClient, _id: int, with_check: bool = True
) -> RequestResult:
    response, data = await api_request(
        client,
        RequestMethods.get,
        ApiRoutes.templates,
        route_detail=f"/{_id}",
    )

    return response, data


async def create_template(
    client: TestClient,
    content: str = "Some content",
    is_base: bool = False,
    search_params: dict | None = None,
) -> RequestResult:
    info = {
        "name": uuid4().hex,
        "slug": f"test-{uuid4().hex}",
        "title": "someTitle",
        "content": content,
        "isBase": is_base,
        "searchParams": search_params,
    }
    response, data = await api_request(
        client, RequestMethods.post, ApiRoutes.templates, data=info
    )

    return response, data


async def update_template(client: TestClient, _id: int, data: dict) -> RequestResult:
    response, data = await api_request(
        client,
        RequestMethods.put,
        ApiRoutes.templates,
        route_detail=f"/{_id}",
        data=data,
    )

    return response, data


async def delete_template(client: TestClient, _id: int) -> RequestResult:
    response, data = await api_request(
        client,
        RequestMethods.delete,
        ApiRoutes.templates,
        route_detail=f"/{_id}",
    )

    return response, data


async def render_template(client: TestClient, _id: int) -> RequestResult:
    response, data = await api_request(
        client,
        RequestMethods.post,
        ApiRoutes.templates,
        route_detail=f"/{_id}/render",
    )

    return response, data
