from datetime import datetime
from uuid import UUID

from pydantic import Field, root_validator, validator

from internal.templates import wrapping
from schemas.base import IdMixin, ListModel, Model
from utils.validators import slug_validator


class TemplateBase(Model):
    slug: str = Field(
        ...,
        max_length=128,
        description="служебное название для шаблона, по которому будут создаваться уведомления. "
        "Используется в uri запроса. "
        'Начинается с буквы на латинице, может содержать латинские буквы, цифры и символ "-"',
    )
    name: str = Field(..., max_length=512)
    title: str = Field(
        ...,
        max_length=256,
        description="Заголовок уведомления, отправляемый пользователям. Также является шаблоном",
    )
    content: str = Field(
        ...,
        description="Шаблон уведомления по которому будут собираться сами уведомления. "
        "Работает на основе шаблонизатора jinja2",
    )
    is_base: bool = Field(
        False,
        description="Является ли шаблон базовым (обёрткой для всех других шаблонов). "
        "Для таких шаблонов необходимо вручную указывать место,"
        "в которое будет добавляться содержимое сообщений",
    )
    search_params: dict | None = Field(
        None,
        description="Доп. значения для фильтрации при get запросах. "
        "Пока что поддерживаются только примитивные типы",
        example={"department_id": 3, "user_id": 20},
    )


class TemplateUpdate(TemplateBase):
    @root_validator()
    def wrap_content(cls, values: dict):
        if not values["is_base"]:
            values["content"] = wrapping.wrap_template(values["content"])
        return values

    @root_validator()
    def rename_base_template(cls, values: dict):
        if values["is_base"]:
            values["slug"] = wrapping.BASE_TEMPLATE_NAME

        return values

    @root_validator()
    def base_template_content_block_set(cls, values: dict):
        if values["is_base"]:
            content_block = wrapping.content_block("")
            if content_block not in values["content"]:
                raise ValueError(
                    f"В базовом шаблоне должно быть указано место для вставки значений. "
                    f'Для указания места вставки используйте конструкцию "{content_block}"'
                )

        return values

    @validator("slug")
    def validate_slug(cls, v):
        try:
            slug_validator(v)
        except ValueError:
            raise ValueError("Некорректное служебное название")
        return v

    @validator("search_params")
    def validate_search_params(cls, search_params: dict | None):
        if search_params:
            supporting_types = {int, float, str, bool}
            for name, value in search_params.items():
                if type(value) not in supporting_types:
                    raise ValueError(
                        f'Type of search parameter "{name}" is not supported. '
                        f"It can be one of {', '.join([i.__name__ for i in supporting_types])}"
                    )
        return search_params


class TemplateBare(TemplateBase, IdMixin):
    """
    Предполагается, что вы сериализуете объект из БД,
    поэтому для отображения пользователю будет обрезана обёртка в базовый шаблон
    """

    id: int
    created_by: UUID | None
    created_at: datetime | None
    updated_by: UUID | None
    updated_at: datetime | None

    @root_validator()
    def unwrap_content(cls, values: dict):
        if not values["is_base"] and wrapping.is_wrapped(values["content"]):
            values["content"] = wrapping.unwrap_template(values["content"])

        return values

    class Config:
        orm_mode = True


class TemplateList(ListModel):
    data: list[TemplateBare]
