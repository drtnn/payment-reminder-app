import logging
import uuid
from inspect import signature
from typing import TypeVar, Callable, Optional, List, Union

from fastapi import Depends, APIRouter, HTTPException
from fastapi.requests import Request
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

logger = logging.getLogger(__name__)

Model = TypeVar("Model")
Identifier = Union[uuid.UUID.__class__, int.__class__, str.__class__]


class CRUDRouter:
    prefix: str

    model: Model
    id_type: Identifier

    kwargs: dict

    get_session: Callable
    get_authentication: Callable

    request_schema: BaseModel.__class__
    create_request_schema: BaseModel.__class__
    update_request_schema: BaseModel.__class__
    partial_update_request_schema: BaseModel.__class__

    response_schema: BaseModel.__class__
    retrieve_response_schema: BaseModel.__class__
    list_response_schema: BaseModel.__class__
    create_response_schema: BaseModel.__class__
    update_response_schema: BaseModel.__class__
    partial_update_response_schema: BaseModel.__class__

    api_router: APIRouter

    @staticmethod
    def get_retrieve_url_pattern(prefix: str) -> str:
        return "/%s/{id}" % prefix

    @staticmethod
    def get_list_url_pattern(prefix: str) -> str:
        return "/%s" % prefix

    @staticmethod
    def get_delete_url_pattern(prefix: str) -> str:
        return "/%s/{id}" % prefix

    @staticmethod
    def get_create_url_pattern(prefix: str) -> str:
        return "/%s" % prefix

    @staticmethod
    def get_update_url_pattern(prefix: str) -> str:
        return "/%s/{id}" % prefix

    @staticmethod
    def get_partial_update_url_pattern(prefix: str) -> str:
        return "/%s/{id}" % prefix

    async def perform_retrieve(self, id: Identifier, session: AsyncSession, *args, **kwargs) -> Model:
        query = await session.execute(select(self.model).where(self.model.id == id))
        if instance := query.scalars().first():
            return instance
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    async def perform_list(self, session: AsyncSession, *args, **kwargs) -> Model:
        query = await session.execute(select(self.model))
        return query.scalars().all()

    async def perform_delete(self, id: Identifier, session: AsyncSession, *args, **kwargs):
        await session.execute(delete(self.model).where(self.model.id == id))
        await session.commit()

    async def perform_create(self, data: BaseModel, session: AsyncSession, *args, **kwargs) -> Model:
        instance = self.model(**data.dict())
        session.add(instance)
        await session.commit()
        return instance

    async def perform_update(self, id: Identifier, data: BaseModel, session: AsyncSession, *args, **kwargs) -> Model:
        instance = await self.perform_retrieve(id=id, session=session, *args, **kwargs)
        for key, value in data.dict().items():
            setattr(instance, key, value)
        await session.commit()
        return instance

    async def perform_partial_update(
            self, id: Identifier, data: BaseModel, session: AsyncSession, *args, **kwargs
    ) -> Model:
        instance = await self.perform_retrieve(id=id, session=session, *args, **kwargs)
        for key, value in data.dict(exclude_none=True, exclude_unset=True).items():
            setattr(instance, key, value)
        await session.commit()
        return instance

    def __init__(
            self,
            prefix: str,
            id_type: Identifier,
            model: Model.__class__,
            get_session: Callable,
            get_authentication: Callable,
            request_schema: Optional[BaseModel.__class__] = None,
            create_request_schema: Optional[BaseModel.__class__] = None,
            update_request_schema: Optional[BaseModel.__class__] = None,
            partial_update_request_schema: Optional[BaseModel.__class__] = None,
            response_schema: Optional[BaseModel.__class__] = None,
            retrieve_response_schema: Optional[BaseModel.__class__] = None,
            list_response_schema: Optional[BaseModel.__class__] = None,
            create_response_schema: Optional[BaseModel.__class__] = None,
            update_response_schema: Optional[BaseModel.__class__] = None,
            partial_update_response_schema: Optional[BaseModel.__class__] = None,
            **kwargs
    ):
        self.prefix = prefix
        self.model = model
        self.id_type = id_type
        self.kwargs = kwargs
        self.get_session = get_session
        self.get_authentication = get_authentication

        authentication_return_type = signature(self.get_authentication).return_annotation

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
        self.list_response_schema = List[response_schema]
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

        async def retrieve(
                request: Request,
                id: self.id_type,  # type: ignore
                session: AsyncSession = Depends(self.get_session),
                auth_token: authentication_return_type = Depends(self.get_authentication)
        ) -> self.retrieve_response_schema:  # type: ignore
            logger.info(f"Пришел запрос на получение сущности типа {self.model.__name__} с id {id}")
            try:
                response = await self.perform_retrieve(id=id, session=session, request=request, auth_token=auth_token)
            except Exception as e:
                logger.error(f"Ошибка при получении объекта типа {self.model.__name__}: {e}")
                raise e
            logger.info(f"Объект типа {self.model.__name__} с id {id} успешно получен")
            return response

        async def list(
                request: Request,
                session: AsyncSession = Depends(self.get_session),
                auth_token: authentication_return_type = Depends(self.get_authentication)
        ) -> self.list_response_schema:  # type: ignore
            logger.info(f"Пришел завпрос на получение списка сущностей типа {self.model.__name__}")
            try:
                response = await self.perform_list(session=session, request=request, auth_token=auth_token)
            except Exception as e:
                logger.error(f"Ошибка при получении списка объектов типа {self.model.__name__}: {e}")
                raise e
            logger.info(f"Список объектов типа {self.model.__name__} успешно получен")
            return response

        async def delete(
                request: Request,
                id: self.id_type,  # type: ignore
                session: AsyncSession = Depends(self.get_session),
                auth_token: authentication_return_type = Depends(self.get_authentication)
        ):
            logger.info(f"Пришел завпрос на удаление сущности типа {self.model.__name__}")
            try:
                await self.perform_delete(id=id, session=session, request=request, auth_token=auth_token)
            except Exception as e:
                logger.error(f"Ошибка при удалении объекта типа {self.model.__name__}: {e}")
                raise e
            logger.info(f"Cущность типа {self.model.__name__} успешно удалена")

        async def create(
                request: Request,
                data: self.create_request_schema,  # type: ignore
                session: AsyncSession = Depends(self.get_session),
                auth_token: authentication_return_type = Depends(self.get_authentication)
        ) -> self.create_response_schema:  # type: ignore
            logger.info(f"Пришел запрос на создание сущности типа {self.model.__name__}: {data}")
            try:
                response = await self.perform_create(data=data, session=session, request=request, auth_token=auth_token)
            except Exception as e:
                logger.error(f"Ошибка при создании объекта типа {self.model.__name__}: {e}")
                raise e
            logger.info(f"Cущность типа {self.model.__name__} успешно создана: {response}")
            return response

        async def update(
                request: Request,
                id: self.id_type,  # type: ignore
                data: self.update_request_schema,  # type: ignore
                session: AsyncSession = Depends(self.get_session),
                auth_token: authentication_return_type = Depends(self.get_authentication)
        ) -> self.update_response_schema:  # type: ignore
            logger.info(f"Пришел запрос на обновление сущности типа {self.model.__name__} с id {id}: {data}")
            try:
                response = await self.perform_update(
                    id=id, data=data, session=session, request=request, auth_token=auth_token
                )
            except Exception as e:
                logger.error(f"Ошибка при обновлении объекта типа {self.model.__name__} с id {id}: {e}")
                raise e
            logger.info(f"Cущность типа {self.model.__name__} с id {id} успешно обновлена: {response}")
            return response

        async def partial_update(
                request: Request,
                id: self.id_type,  # type: ignore
                data: self.partial_update_request_schema,  # type: ignore
                session: AsyncSession = Depends(self.get_session),
                auth_token: authentication_return_type = Depends(self.get_authentication)
        ) -> self.partial_update_response_schema:  # type: ignore
            logger.info(f"Пришел запрос на частичное обновление сущности типа {self.model.__name__} с id {id}: {data}")
            try:
                response = await self.perform_partial_update(
                    id=id, data=data, session=session, request=request, auth_token=auth_token
                )
            except Exception as e:
                logger.error(f"Ошибка при частичное обновлении объекта типа {self.model.__name__} с id {id}: {e}")
                raise e
            logger.info(f"Cущность типа {self.model.__name__} с id {id} успешно частично обновлена: {response}")
            return response

        self.api_router = APIRouter()

        self.api_router.get(
            path=self.get_retrieve_url_pattern(prefix=prefix), response_model=self.retrieve_response_schema,
            status_code=status.HTTP_200_OK
        )(retrieve)
        self.api_router.get(
            path=self.get_list_url_pattern(prefix=prefix), response_model=self.list_response_schema,
            status_code=status.HTTP_200_OK
        )(list)
        self.api_router.delete(
            path=self.get_delete_url_pattern(prefix=prefix),
            status_code=status.HTTP_204_NO_CONTENT
        )(delete)
        self.api_router.post(
            path=self.get_create_url_pattern(prefix=prefix), response_model=self.create_response_schema,
            status_code=status.HTTP_201_CREATED
        )(create)
        self.api_router.put(
            path=self.get_update_url_pattern(prefix=prefix), response_model=self.update_response_schema,
            status_code=status.HTTP_200_OK
        )(update)
        self.api_router.patch(
            path=self.get_partial_update_url_pattern(prefix=prefix), response_model=self.partial_update_response_schema,
            status_code=status.HTTP_200_OK
        )(partial_update)
