from datetime import datetime
from typing import Any

from pydantic import Field, root_validator, validator

from models import (
    Backend,
    NotificationRecurrenceFrequency,
    NotificationRecurrenceWeekday,
)
from schemas.base import ListModel, Model, UidMixin


class NotificationRecurrenceBase(Model):
    frequency: NotificationRecurrenceFrequency = Field(
        ..., description="Частота повторения уведомления"
    )
    started_at: datetime = Field(
        ..., description="Дата, начиная с которой будут повторяться уведомления"
    )
    interval: int = Field(
        default=1, description="Интервал между каждой итерацией повторения"
    )
    count: int | None = Field(
        None,
        description="Сколько раз должно повториться уведомление (допустимо указывать без until)",
    )
    until: datetime | None = Field(
        None,
        description="Дата, до которой уведомление будет повторяться (допустимо указывать без count)",
    )
    week_days: list[NotificationRecurrenceWeekday] = Field(
        default_factory=list,
        description="Дни недели, в которые будет применяться повторение",
    )
    additional_dates: list[datetime] = Field(
        default_factory=list,
        description="Дополнительные даты уведомления, которые не входят в основное правило",
    )
    exclude_dates: list[datetime] = Field(
        default_factory=list,
        description="Даты, которые нужно исключить из основного правила",
    )

    class Config(Model.Config):
        orm_mode = True


class NotificationRecurrenceCreate(NotificationRecurrenceBase):
    @root_validator()
    def check_stop_recurrence(cls, values):
        count = values.get("count")
        until = values.get("until")

        if not count and not until:
            raise ValueError(
                "Необходимо указать количество повторений или дату завершения повторений уведомления"
            )

        if count and until:
            raise ValueError(
                "Необходимо указать только один из параметров повторения: "
                "количество или дату завершения повторов"
            )

        return values

    @root_validator()
    def convert_dates(cls, values):
        until = values.get("until")

        values["additional_dates"] = [
            i.replace(tzinfo=None) for i in values.get("additional_dates")
        ]
        values["exclude_dates"] = [
            i.replace(tzinfo=None) for i in values.get("exclude_dates")
        ]
        values["started_at"] = values.get("started_at").replace(tzinfo=None)
        values["until"] = until.replace(tzinfo=None) if until else None

        return values


class NotificationRecurrenceBrief(NotificationRecurrenceBase):
    id: int

    @root_validator()
    def hide_until_with_count(cls, values):
        until = values.get("until")
        count = values.get("count")

        if until and count:
            values["until"] = None

        return values


class NotificationCreate(Model):
    user_id: int | None = Field(
        default=None,
        description="Идентификатор пользователя при директивной отправке уведомления",
    )
    contacts: dict[Backend, str | None] = Field(
        default=None,
        description="Данные по которым будут отправлены уведомления. "
        "Может быть почтой/никнеймом или чем-то другим, "
        "в зависимости от платформы в которой будут отправлены уведомления."
        "То, на какую платформу будет отправлено уведомление зависит от переданных данных",
        example={
            Backend.email.value: "myemail@uriit.ru",
            Backend.sms.value: "Можно ничего и не указывать. Или id пользователя",
        },
    )
    template_data: dict[str, Any] = Field(
        ...,
        description="Переменные для подстановки в шаблон уведомления",
        example={
            "user_full_name": "Петров В.В.",
            "issue": "Оформление займа в залог недвижимости",
        },
    )

    recurrence: NotificationRecurrenceCreate | None = Field(
        None, description="Правила повторения уведомления для регулярных уведомлений"
    )

    @validator("user_id")
    def check_contacts_on_user_id(cls, value, values):
        contacts = values.get("contacts")
        if value and contacts:
            return value

        raise ValueError(
            "При директивной отправке уведомления необходимо указывать контакты пользователя"
        )

    class Config:
        use_enum_values = True


class NotificationCreateBatch(Model):
    data: list[NotificationCreate]


class NotificationBare(NotificationCreate, UidMixin):
    class Config:
        orm_mode = True


class NotificationsList(ListModel):
    data: list[NotificationBare]
