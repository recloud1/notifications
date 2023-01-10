import dataclasses
from typing import ClassVar

import fastapi
import sentry_sdk
import starlette
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from starlette.middleware.base import (
    BaseHTTPMiddleware,
    DispatchFunction,
    RequestResponseEndpoint,
)
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp


@dataclasses.dataclass
class ReceiveProxy:
    """
    Кэширование тела запроса при его получении из объекта Request в HTTP Middleware.

    Причина: при вызове метода await request.body() Stream, в который пришел
    данный Request, очищается (как-будто он вернул результат) и ожидает
    новую порцию информации (по сути уходя в вечный цикл)
    Решение взято отсюда: https://github.com/tiangolo/fastapi/issues/394#issuecomment-994665859
    """

    receive: starlette.types.Receive
    cached_body: bytes
    _is_first_call: ClassVar[bool] = True

    async def __call__(self):
        # First call will be for getting request body => returns cached result
        if self._is_first_call:
            self._is_first_call = False
            return {
                "type": "http.request",
                "body": self.cached_body,
                "more_body": False,
            }

        return await self.receive()


async def get_request_body(request: Request) -> bytes:
    body = await request.body()

    request._receive = ReceiveProxy(receive=request.receive, cached_body=body)
    return body


class SentryFullAsgiMiddleware:
    def __init__(self, app: fastapi.FastAPI, initial_status_code: int = 400):
        """
        Промежуточный обработчик (всех HTTP-запросов к FastAPI) в результате которого
        в Sentry отправляется код результата выполнения запроса, а также
        при выбрасывании исключения во время выполнения запроса дополнительно отправляется:
        * URL-адрес, по которому совершается запрос
        * HTTP-глагол
        * Заголовки запроса
        * Query-параметры запроса
        * Тело запроса
        * Форма запроса (при отправки файлов)
        :param app:
        :param initial_status_code:
        """
        self.app = app
        app.add_middleware(
            SentryResponseLoggerMiddleware,
            dispatch=None,
            initial_status_code=initial_status_code,
        )
        app.add_middleware(SentryAsgiMiddleware)


class SentryResponseLoggerMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        dispatch: DispatchFunction = None,
        initial_status_code: int = 400,
    ) -> None:
        """
        Важно, чтобы данный Middleware выполнялся последним в цепочке (т.е. его регистрация в FastAPI должна быть
        первой). Причина: данный обработчик опирается на SentryAsgiMiddleware, в котором создается транзакция
        Sentry (именно к ней нужно добавлять информацию в данном Middleware) => необходимо
        чтобы SentryAsgiMiddleware обработал до данного Middleware
        param: initial_status_code: код ответа, начиная с которого в sentry будет отсылаться тело запроса
        """
        self.initial_status_code = initial_status_code
        self.sentry_asgi_middleware = SentryAsgiMiddleware(app)
        super().__init__(app, dispatch)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        scope = sentry_sdk.Hub.current.scope
        transaction = scope.transaction

        body = await get_request_body(request)
        form = await request.form()
        response = await call_next(request)
        status_code = response.status_code

        if not await request.is_disconnected():
            transaction.set_http_status(status_code)
            if status_code >= self.initial_status_code:
                scope.set_context(
                    "Request Information",
                    {
                        "url": str(request.url),
                        "method": request.method,
                        "path_params": request.path_params,
                        "headers": request.headers,
                        "body": body,
                        "form": form,
                    },
                )
        return response
