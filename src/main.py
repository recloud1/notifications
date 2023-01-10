import fastapi
from starlette.middleware.cors import CORSMiddleware

from core.config import envs
from core.log_config import set_logging
from routes.exceptions import apply_exception_handlers
from routes.v1.templates import templates

app = fastapi.FastAPI(
    title="Notification Service",
    description="Сервис уведомлений онлайн-кинотеатра",
    swagger_ui_parameters={"docExpansion": "none"},
)

set_logging(
    level=envs.logging.level,
    sentry_url=envs.logging.sentry_url,
    environment=envs.app.environment,
    app=app,
)

apply_exception_handlers(app)


if not envs.app.cors_policy_enabled:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Disposition"],
        allow_credentials=True,
    )

app.include_router(templates, prefix="/v1/templates", tags=["Templates"])
# app.include_router(bookmarks, prefix="/v1/bookmarks", tags=["Bookmarks"])
# app.include_router(likes, prefix="/v1/likes", tags=["Likes"])
# app.include_router(reviews, prefix="/v1/reviews", tags=["Reviews"])
