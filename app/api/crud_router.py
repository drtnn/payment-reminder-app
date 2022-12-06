from typing import TypeVar, Callable, Optional

from fastapi import Depends, APIRouter
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.models import AuthToken

Model = TypeVar("Model")

IdType = TypeVar("IdType")


class CRUDRouter:
    model: Model

    id_type: IdType

    prefix: str

    get_session: Callable
    get_auth_token: Callable

    request_schema: BaseModel
    create_request_schema: BaseModel
    update_request_schema: BaseModel
    partial_update_request_schema: BaseModel

    response_schema: BaseModel
    retrieve_response_schema: BaseModel
    list_response_schema: BaseModel
    create_response_schema: BaseModel
    update_response_schema: BaseModel
    partial_update_response_schema: BaseModel

    api_router: APIRouter

    @staticmethod
    def get_retrieve_url_pattern(prefix: str):
        return "/%s/{id}" % prefix

    @staticmethod
    def get_list_url_pattern(prefix: str):
        return "/%s" % prefix

    @staticmethod
    def get_delete_url_pattern(prefix: str):
        return "/%s/{id}" % prefix

    @staticmethod
    def get_create_url_pattern(prefix: str):
        return "/%s" % prefix

    @staticmethod
    def get_update_url_pattern(prefix: str):
        return "/%s/{id}" % prefix

    @staticmethod
    def get_partial_update_url_pattern(prefix: str):
        return "/%s/{id}" % prefix

    def __init__(
            self,
            model: Model.__class__,
            id_type: IdType,
            prefix: str,
            get_session: Callable,
            get_auth_token: Callable,
            request_schema: Optional[BaseModel.__class__] = None,
            create_request_schema: Optional[BaseModel.__class__] = None,
            update_request_schema: Optional[BaseModel.__class__] = None,
            partial_update_request_schema: Optional[BaseModel.__class__] = None,
            response_schema: Optional[BaseModel.__class__] = None,
            retrieve_response_schema: Optional[BaseModel.__class__] = None,
            list_response_schema: Optional[BaseModel.__class__] = None,
            create_response_schema: Optional[BaseModel.__class__] = None,
            update_response_schema: Optional[BaseModel.__class__] = None,
            partial_update_response_schema: Optional[BaseModel.__class__] = None
    ):
        self.model = model
        self.id_type = id_type
        self.prefix = prefix
        self.get_session = get_session
        self.get_auth_token = get_auth_token

        self.request_schema = request_schema
        self.create_request_schema = request_schema
        self.update_request_schema = request_schema
        self.partial_update_request_schema = request_schema

        if create_request_schema:
            self.create_request_schema = create_request_schema
        if update_request_schema:
            self.update_request_schema = update_request_schema
        if partial_update_request_schema:
            self.partial_update_request_schema = partial_update_request_schema

        if not (self.create_request_schema and self.update_request_schema and self.partial_update_request_schema):
            raise ValueError(
                "create_request_schema, update_request_schema and partial_update_request_schema must not be None"
            )

        self.response_schema = response_schema
        self.retrieve_response_schema = response_schema
        self.list_response_schema = response_schema
        self.create_response_schema = response_schema
        self.update_response_schema = response_schema
        self.partial_update_response_schema = response_schema

        if retrieve_response_schema:
            self.retrieve_response_schema = retrieve_response_schema
        if list_response_schema:
            self.list_response_schema = list_response_schema
        if create_response_schema:
            self.create_response_schema = create_response_schema
        if update_response_schema:
            self.update_response_schema = update_response_schema
        if partial_update_response_schema:
            self.partial_update_response_schema = partial_update_response_schema

        if not (
                self.retrieve_response_schema and self.list_response_schema and self.create_response_schema
                and self.update_response_schema and self.partial_update_response_schema
        ):
            raise ValueError(
                "retrieve_response_schema, list_response_schema, create_response_schema, update_response_schema and "
                "partial_update_response_schema must not be None"
            )

        def retrieve(
                id: self.id_type,  # type: ignore
                session: AsyncSession = Depends(self.get_session),
                auth_token: AuthToken = Depends(self.get_auth_token)
        ) -> self.retrieve_response_schema:  # type: ignore
            pass

        def list(
                session: AsyncSession = Depends(self.get_session),
                auth_token: AuthToken = Depends(self.get_auth_token)
        ) -> self.list_response_schema:  # type: ignore
            pass

        def delete(
                id: self.id_type,  # type: ignore
                session: AsyncSession = Depends(self.get_session),
                auth_token: AuthToken = Depends(self.get_auth_token)
        ):
            pass

        def create(
                data: self.create_request_schema,  # type: ignore
                session: AsyncSession = Depends(self.get_session),
                auth_token: AuthToken = Depends(self.get_auth_token)
        ) -> self.create_response_schema:  # type: ignore
            pass

        def update(
                id: self.id_type,  # type: ignore
                data: self.update_request_schema,  # type: ignore
                session: AsyncSession = Depends(self.get_session),
                auth_token: AuthToken = Depends(self.get_auth_token)
        ) -> self.update_response_schema:  # type: ignore
            pass

        def partial_update(
                id: self.id_type,  # type: ignore
                data: self.update_request_schema,  # type: ignore
                session: AsyncSession = Depends(self.get_session),
                auth_token: AuthToken = Depends(self.get_auth_token)
        ) -> self.partial_update_response_schema:  # type: ignore
            pass

        self.api_router = APIRouter()

        # TODO: fill parameters
        self.api_router.post(
            path=self.get_create_url_pattern(prefix=prefix), response_model=self.create_response_schema,
            status_code=status.HTTP_201_CREATED
        )(create)
        self.api_router.get(
            path=self.get_retrieve_url_pattern(prefix=prefix), response_model=self.retrieve_response_schema,
            status_code=status.HTTP_200_OK
        )(retrieve)
        self.api_router.delete(
            path=self.get_delete_url_pattern(prefix=prefix),
            status_code=status.HTTP_204_NO_CONTENT
        )(delete)
        self.api_router.put(
            path=self.get_update_url_pattern(prefix=prefix), response_model=self.update_response_schema,
            status_code=status.HTTP_200_OK
        )(update)
        self.api_router.patch(
            path=self.get_partial_update_url_pattern(prefix=prefix), response_model=self.partial_update_response_schema,
            status_code=status.HTTP_200_OK
        )(partial_update)
