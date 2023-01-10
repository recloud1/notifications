import enum
from datetime import datetime

import dateutil.rrule as rrule
import sqlalchemy
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import relationship

from models import Base, fresh_timestamp

DB_SCHEMA = "notifications"


def with_schema(tablename: str) -> str:
    """
    Небольшой хелпер для указания таблиц в качестве foreign key.

    :param tablename: название таблицы
    :return: объединенное название схемы и таблицы
    """
    return f"{DB_SCHEMA}.{tablename}"


class Template(Base):
    __repr_name__ = "Шаблон"
    __tablename__ = "templates"
    __table_args__ = {"schema": DB_SCHEMA}

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    slug: str = Column(
        String(128), nullable=False, comment="Уникальное название для шаблона"
    )

    name: str = Column(String(512), nullable=False)
    title: str = Column(String(256), nullable=False)
    is_base = Column(
        Boolean,
        default=False,
        comment="Является ли шаблон базовым",
        nullable=False,
    )
    content = Column(Text, nullable=False)
    variables = Column(JSONB)

    search_params = Column(JSONB, comment="Все поля доп. фильтрации")

    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)

    created_at = Column(DateTime, default=fresh_timestamp())
    updated_at = Column(DateTime, default=fresh_timestamp(), onupdate=fresh_timestamp())


class Notification(Base):
    __repr_name__ = "Уведомление"
    __tablename__ = "notifications"
    __table_args__ = {"schema": DB_SCHEMA}

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()")
    )
    user_id = Column(Integer, nullable=True)
    contacts = Column(
        JSONB,
        nullable=True,
        comment="Словарь с данными для отправки уведомления во всех backend'ах для конкретного пользователя",
    )
    template_data = Column(JSONB)
    template_id = Column(
        Integer,
        ForeignKey(with_schema("templates.id"), ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    recurrence_id: int = Column(
        Integer,
        ForeignKey(with_schema("recurrences.id")),
        nullable=True,
        comment="Правила повторения для регулярных оповещений",
    )

    created_at = Column(DateTime, default=fresh_timestamp())
    created_by = Column(UUID(as_uuid=True), nullable=True)

    template: Template = relationship("Template")

    recurrence: "NotificationRecurrence" = relationship(
        "NotificationRecurrence", uselist=False
    )


class Backend(enum.Enum):
    email = "email"
    sms = "sms"


BackendEnum = sqlalchemy.Enum(Backend, schema=DB_SCHEMA)


class NotificationMessage(Base):
    __repr_name__ = "Сообщение"
    __tablename__ = "notification_messages"
    __table_args__ = (
        Index("ix_user_id_backends", "user_id", "backend"),
        {"schema": DB_SCHEMA},
    )

    id = Column(UUID, primary_key=True, server_default=text("uuid_generate_v4()"))
    user_id = Column(Integer, nullable=False)  # осознанная денормализация
    send_to = Column(Text, nullable=False)
    notification_id = Column(
        UUID,
        ForeignKey(with_schema("notifications.id"), ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    backend = Column(BackendEnum, nullable=False)

    sent_at = Column(DateTime)
    read_at = Column(DateTime, comment="Дата прочтения уведомления")
    created_at = Column(DateTime, default=fresh_timestamp())


class NotificationRecurrenceFrequency(enum.Enum):
    YEARLY = rrule.YEARLY
    MONTHLY = rrule.MONTHLY
    WEEKLY = rrule.WEEKLY
    DAILY = rrule.DAILY
    HOURLY = rrule.HOURLY
    MINUTELY = rrule.MINUTELY
    SECONDLY = rrule.SECONDLY


class NotificationRecurrenceWeekday(enum.Enum):
    MO = rrule.MO.weekday
    TU = rrule.TU.weekday
    WE = rrule.WE.weekday
    TH = rrule.TH.weekday
    FR = rrule.FR.weekday
    SA = rrule.SA.weekday
    SU = rrule.SU.weekday


class NotificationRecurrence(Base):
    __repr_name__ = "Правило повторения оповещения"
    __tablename__ = "recurrences"
    __table_args__ = {"schema": DB_SCHEMA, "comment": "правила повторения оповещения"}

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    frequency: NotificationRecurrenceFrequency = Column(
        Enum(NotificationRecurrenceFrequency, name="frequencies"),
        nullable=False,
        comment="Частота повторения оповещения",
    )
    started_at: datetime = Column(
        DateTime,
        nullable=False,
        comment="Дата, начиная с которой будут повторяться оповещения",
    )
    interval: int = Column(
        Integer, nullable=False, comment="Интервал между каждой итерацией повторения"
    )
    count: int = Column(
        Integer,
        nullable=True,
        comment="Сколько раз должно повториться оповещение (если данный параметр указан, "
        "то дополнительно вычисляется until)",
    )
    until: datetime = Column(
        DateTime, nullable=True, comment="Дата, до которой оповещения будет повторяться"
    )
    week_days: list[int] = Column(
        ARRAY(Integer),
        nullable=True,
        comment="Дни недели, в которые будет применяться повторение",
    )
    additional_dates: list[datetime] = Column(
        ARRAY(DateTime),
        nullable=True,
        comment="Дополнительные даты оповещений, которые не входят в основное правило",
    )
    exclude_dates: list[datetime] = Column(
        ARRAY(DateTime),
        nullable=True,
        comment="Даты, которые нужно исключить из основного правила",
    )
