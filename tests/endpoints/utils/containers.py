import pathlib

import alembic.config
from alembic import command
from testcontainers.postgres import PostgresContainer


def run_alembic_migrations(container: PostgresContainer):
    """
    Запуск миграций проекта.

    Конфигурация описана исходя из структуры текущего проекта
    """
    base_dir = pathlib.Path("../")
    migrations_dir = base_dir / "migrations"
    alembic_ini_location = base_dir / "alembic.ini"

    alembic_cfg = alembic.config.Config(str(alembic_ini_location))
    alembic_cfg.set_main_option("script_location", str(migrations_dir))
    alembic_cfg.set_main_option("sqlalchemy.url", container.get_connection_url())

    command.upgrade(alembic_cfg, "head")
