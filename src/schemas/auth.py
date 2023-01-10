from uuid import UUID

from schemas.base import Model


class UserInfo(Model):
    """
    Данные, хранящиеся в JWT токене
    """

    id: UUID
    role_id: UUID | None
    role_name: str | None
