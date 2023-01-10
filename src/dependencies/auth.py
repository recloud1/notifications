from aiohttp import ClientSession
from fastapi import Depends, security

from core.config import envs
from schemas.auth import UserInfo


def jwt_token_dep(
    token: security.HTTPAuthorizationCredentials = Depends(
        security.HTTPBearer(bearerFormat="Bearer")
    ),
) -> str:
    return token.credentials


async def user_authorized(token: str = Depends(jwt_token_dep)) -> UserInfo:
    """
    Зависимость для работы с разрешениями для http endpoint'ов.
    """
    url = envs.external.auth
    data = {"token": token}
    async with ClientSession() as session:
        async with session.post(url=url, json=data) as response:
            data = await response.json()
            result = UserInfo(**data)

            return result


user_info_dep = Depends(user_authorized)
