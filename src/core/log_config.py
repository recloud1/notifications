import logging

import sentry_sdk
from fastapi import FastAPI
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from utils.sentry import SentryFullAsgiMiddleware


def set_logging(
    level=logging.DEBUG,
    sentry_url: str = None,
    environment: str = "TEST_LOCAL",
    app: FastAPI = None,
):
    """
    Устанавливает конфигурацию для логирования
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        force=True,
    )

    if sentry_url:
        sentry_logging = LoggingIntegration(level=level, event_level=logging.ERROR)

        if app is not None:
            SentryFullAsgiMiddleware(app)

        try:
            sentry_sdk.init(
                sentry_url,
                traces_sample_rate=1.0,
                environment=environment,
                integrations=[sentry_logging, SqlalchemyIntegration()],
            )
        except Exception as e:
            logging.warning(
                f"Connect to sentry failed. Type Error: {type(e)}, {str(e)}"
            )
