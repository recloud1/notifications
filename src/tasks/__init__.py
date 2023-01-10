import functools

import aiomisc
import dramatiq
from dramatiq.brokers.rabbitmq import RabbitmqBroker
from pika import PlainCredentials

from core.config import Config, RabbitmqConfig
from utils.log_config import set_logging

set_logging(
    level=Config.log_level,
    enable_additional_debug=Config.additional_debug,
    sentry_url=Config.sentry_url,
    environment=Config.environment,
)

RabbitmqConfig.ensure_configured()
rabbitmq_broker = RabbitmqBroker(
    host=RabbitmqConfig.rabbit_host,
    port=RabbitmqConfig.rabbit_port,
    credentials=PlainCredentials(
        username=RabbitmqConfig.rabbit_user, password=RabbitmqConfig.rabbit_password
    ),
    heartbeat=600,
)

dramatiq.set_broker(rabbitmq_broker)


class AsyncActor(dramatiq.Actor):
    @aiomisc.threaded
    def send(self, *args, **kwargs):
        return super().send(*args, **kwargs)


dramatiq.actor = functools.partial(dramatiq.actor, actor_class=AsyncActor)


@dramatiq.actor
def example():
    print("HOLA")
