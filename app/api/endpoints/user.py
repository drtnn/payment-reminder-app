from fastapi import APIRouter

from app.api.crud_router import ModelCRUDRouter
from app.api.deps import get_session, BearerTokenAuthentication
from app.models import User
from app.schemas.user import UserSchema, UserCreateRequestSchema

router = APIRouter()

token_authentication = BearerTokenAuthentication()

user_crud_router = ModelCRUDRouter(
    prefix="user",
    model=User,
    identifier_type=int,
    get_session=get_session,
    get_authentication=token_authentication,
    request_schema=UserSchema,
    request_create_schema=UserCreateRequestSchema,
    response_schema=UserSchema
)

router.include_router(user_crud_router.api_router)
