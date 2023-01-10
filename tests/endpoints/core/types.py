from typing import TypeVar

from starlette.responses import Response

RequestResult = TypeVar("RequestResult", bound=tuple[Response, dict])
