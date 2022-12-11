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


async def get_authentication_token(session: AsyncSession, authorization: str) -> Optional[AuthToken]:
    token = authorization.replace(BearerTokenAuthentication.BEARER, "").strip()
    auth_token: Optional[AuthToken] = (await session.execute(select(AuthToken).where(AuthToken.id == token))).first()
    return auth_token


class BearerTokenAuthentication:
    auto_error: bool = True

    BEARER: str = "Bearer"
    AUTHORIZATION_REGEX = r"^%s [0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$" % BEARER

    @classmethod
    async def get_authentication(
            cls, request: Request, session: AsyncSession = Depends(get_session)
    ) -> Optional[AuthToken]:
        authorization = request.headers.get("Authorization", "")
        if (
                re.compile(cls.AUTHORIZATION_REGEX).match(authorization)
                and (token := await get_authentication_token(session, authorization))
        ):
            return token
        else:
            if cls.auto_error:
                raise HTTPException(
                    status_code=HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": cls.BEARER},
                )
