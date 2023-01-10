from urllib import parse

from pydantic import BaseSettings


class Settings(BaseSettings):
    class Config:
        env_file = ".env"


class App(Settings):
    host: str = "localhost"
    port: int = 8001
    cors_policy_enabled: bool = False
    environment: str = "LOCAL_TEST"
    test_token: str | None

    class Config(Settings.Config):
        env_prefix = "APP_"


class DBConfig(Settings):
    name: str
    password: str
    host: str
    port: int
    user: str

    @property
    def async_db_conn_str(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{parse.quote(self.password)}@{self.host}:{self.port}/{self.name}"

    class Config(Settings.Config):
        env_prefix = "DB_"


class RabbitmqConfig(Settings):
    host: str
    port: int
    user: str
    password: str

    class Config(Settings.Config):
        env_prefix = "RABBITMQ_"


class External(Settings):
    auth: str

    class Config(Settings.Config):
        env_prefix = "EXTERNAL_"


class LoggingConfig(Settings):
    sentry_url: str | None
    level: str = "DEBUG"

    class Config(Settings.Config):
        env_prefix = "LOGGING_"


class SMTPConfig(Settings):
    server: str
    from_email: str
    login: str
    password: str
    port: str

    class Config(Settings.Config):
        env_prefix = "SMTP_"


class Envs(Settings):
    app: App = App()
    database: DBConfig = DBConfig()
    rabbitmq: RabbitmqConfig = RabbitmqConfig()
    external: External = External()
    logging: LoggingConfig = LoggingConfig()
    smtp: SMTPConfig = SMTPConfig()


envs = Envs()
