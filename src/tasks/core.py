import functools
import logging

import aiomisc
import dramatiq as dramatiq_lib
import pika
from dramatiq.brokers.rabbitmq import RabbitmqBroker

from core.config import envs
from core.log_config import set_logging

# RabbitmqConfig.ensure_configured()
rabbitmq_broker = RabbitmqBroker(
    host=envs.rabbitmq.host,
    port=envs.rabbitmq.port,
    credentials=pika.PlainCredentials(
        username=envs.rabbitmq.user, password=envs.rabbitmq.password
    ),
)
dramatiq_lib.set_broker(rabbitmq_broker)

set_logging(
    level=envs.logging.level,
    sentry_url=envs.loggin.sentry_url,
    environment=envs.app.environment,
)


class AsyncActor(dramatiq_lib.Actor):
    # вынесено для перегрузки в тестах
    MAX_RETRIES = 20
    MIN_BACKOFF = 15 * 1000  # 15s

    def __init__(self, fn, *, broker, actor_name, queue_name, priority, options):

        super().__init__(
            fn,
            broker=broker,
            actor_name=actor_name,
            queue_name=queue_name,
            priority=priority,
            options=options,
        )
        self.logger.setLevel(logging.DEBUG)

    def message_with_options(self, *, args=None, kwargs=None, **options):
        if not options.get("max_retries"):
            options["max_retries"] = self.MAX_RETRIES
        if not options.get("min_backoff"):
            options["min_backoff"] = self.MIN_BACKOFF

        return super().message_with_options(args=args, kwargs=kwargs, **options)

    @aiomisc.threaded
    def send_async(self, *args, **kwargs):
        return super().send(*args, **kwargs)


dramatiq_lib.actor = functools.partial(
    dramatiq_lib.actor,
    actor_class=AsyncActor,
)

dramatiq = dramatiq_lib
