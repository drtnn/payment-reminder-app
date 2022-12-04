import re
from typing import Optional, AsyncGenerator

from fastapi import HTTPException, Depends
from fastapi.requests import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_401_UNAUTHORIZED

from app.core.session import async_session
from app.models import AuthToken


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


async def get_auth_token(session: AsyncSession, authorization: str) -> Optional[AuthToken]:
    token = authorization.replace(BearerTokenAuthorization.BEARER, "").strip()
    auth_token: Optional[AuthToken] = (await session.execute(select(AuthToken).where(AuthToken.key == token))).first()
    return auth_token


class BearerTokenAuthorization:
    auto_error: bool

    BEARER: str = "Bearer"
    AUTHORIZATION_REGEX = r"^%s [0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$" % BEARER

    def __init__(self, auto_error: bool = True):
        self.auto_error = auto_error

    async def __call__(self, request: Request, session: AsyncSession = Depends(get_session)) -> Optional[AuthToken]:
        authorization = request.headers.get("Authorization", "")
        if (
                re.compile(self.AUTHORIZATION_REGEX).match(authorization)
                and (token := await get_auth_token(session, authorization))
        ):
            return token
        else:
            if self.auto_error:
                raise HTTPException(
                    status_code=HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": self.BEARER},
                )
            else:
                return None
