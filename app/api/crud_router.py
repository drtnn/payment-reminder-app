import logging
import uuid
from typing import TypeVar, Callable, Optional, List

from fastapi import Depends, APIRouter, HTTPException
from fastapi.requests import Request
from pydantic import BaseModel
from pydantic.main import ModelMetaclass
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

logger = logging.getLogger(__name__)

Model = TypeVar("Model")
Authentication = TypeVar("Authentication")
IdentifierType = TypeVar("IdentifierType", uuid.UUID.__class__, int.__class__, str.__class__)


class AllOptionalFields(ModelMetaclass):
    def __new__(mcs, name, bases, namespaces, **kwargs):
        annotations = namespaces.get('__annotations__', {})
        for base in bases:
            annotations.update(base.__annotations__)
        for field in annotations:
            if not field.startswith('__'):
                annotations[field] = Optional[annotations[field]]
        namespaces['__annotations__'] = annotations
        return super().__new__(mcs, name, bases, namespaces, **kwargs)


def get_all_optional_fields_model(model: BaseModel.__class__):
    class AllOptionalFieldsModel(model, metaclass=AllOptionalFields):
        pass

    return AllOptionalFieldsModel


class RouterGeneric:
    prefix: str

    model: Model
    identifier_type: IdentifierType

    kwargs: dict

    get_session: Callable
    get_authentication: Callable

    request_schema: Optional[BaseModel.__class__]
    create_request_schema: Optional[BaseModel.__class__]
    update_request_schema: Optional[BaseModel.__class__]
    partial_update_request_schema: Optional[BaseModel.__class__]

    response_schema: Optional[BaseModel.__class__]
    retrieve_response_schema: Optional[BaseModel.__class__]
    list_response_schema: Optional[BaseModel.__class__]
    create_response_schema: Optional[BaseModel.__class__]
    update_response_schema: Optional[BaseModel.__class__]
    partial_update_response_schema: Optional[BaseModel.__class__]

    api_router: APIRouter

    CRUD_ACTIONS: List[str] = ["retrieve", "list", "delete", "create", "update", "partial_update"]

    def __init__(
            self,
            prefix: str,
            identifier_type: IdentifierType,
            model: Model,
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
        self.api_router = APIRouter()
        self.model = model
        self.identifier_type = identifier_type
        self.kwargs = kwargs
        self.get_session = get_session
        self.get_authentication = get_authentication

        self.request_schema = request_schema
        self.create_request_schema = request_schema
        self.update_request_schema = request_schema
        self.partial_update_request_schema = get_all_optional_fields_model(request_schema)

        if create_request_schema:
            self.create_request_schema = create_request_schema
        if update_request_schema:
            self.update_request_schema = update_request_schema
        if partial_update_request_schema:
            self.partial_update_request_schema = partial_update_request_schema

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

        self.__register_actions()

    def __register_actions(self):
        for action in self.CRUD_ACTIONS:
            try:
                register_action = getattr(self, f"register_{action}_action")
            except AttributeError:
                pass
            else:
                register_action()


class RetrieveRouterMixin:
    prefix: str

    model: Model
    identifier_type: IdentifierType

    kwargs: dict

    get_session: Callable
    get_authentication: Callable

    retrieve_response_schema: BaseModel.__class__

    api_router: APIRouter

    @property
    def retrieve_url_pattern(self):
        return "/%s/{id}" % self.prefix

    async def perform_retrieve(self, id: IdentifierType, session: AsyncSession, *args, **kwargs) -> Model:
        query = await session.execute(select(self.model).where(self.model.id == id))
        if instance := query.scalars().first():
            return instance
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    def register_retrieve_action(self, *args, **kwargs):
        if not self.retrieve_response_schema:
            raise ValueError("retrieve_response_schema must not be None")

        async def retrieve(
                request: Request,
                id: self.identifier_type,  # type: ignore
                session: AsyncSession = Depends(self.get_session),
                authentication: Authentication = Depends(self.get_authentication)
        ) -> self.retrieve_response_schema:  # type: ignore
            logger.info(f"Пришел запрос на получение сущности типа {self.model.__name__} с id {id}")
            try:
                response = await self.perform_retrieve(
                    id=id, session=session, request=request, authentication=authentication, *args, **kwargs
                )
            except Exception as e:
                logger.error(f"Ошибка при получении объекта типа {self.model.__name__}: {e}")
                raise e
            logger.info(f"Объект типа {self.model.__name__} с id {id} успешно получен")
            return response

        self.api_router.get(
            path=self.retrieve_url_pattern, response_model=self.retrieve_response_schema,
            status_code=status.HTTP_200_OK
        )(retrieve)


class ListRouterMixin:
    prefix: str

    model: Model
    identifier_type: IdentifierType

    kwargs: dict

    get_session: Callable
    get_authentication: Callable

    list_response_schema: BaseModel.__class__

    api_router: APIRouter

    @property
    def list_url_pattern(self) -> str:
        return "/%s" % self.prefix

    async def perform_list(self, session: AsyncSession, *args, **kwargs) -> Model:
        query = await session.execute(select(self.model))
        return query.scalars().all()

    def register_list_action(self, *args, **kwargs):
        if not self.list_response_schema:
            raise ValueError("list_response_schema must not be None")

        async def list(
                request: Request,
                session: AsyncSession = Depends(self.get_session),
                authentication: Authentication = Depends(self.get_authentication)  # type: ignore
        ) -> self.list_response_schema:  # type: ignore
            logger.info(f"Пришел завпрос на получение списка сущностей типа {self.model.__name__}")
            try:
                response = await self.perform_list(
                    session=session, request=request, authentication=authentication, *args, **kwargs
                )
            except Exception as e:
                logger.error(f"Ошибка при получении списка объектов типа {self.model.__name__}: {e}")
                raise e
            logger.info(f"Список объектов типа {self.model.__name__} успешно получен")
            return response

        self.api_router.get(
            path=self.list_url_pattern, response_model=self.list_response_schema,
            status_code=status.HTTP_200_OK
        )(list)


class DeleteRouterMixin:
    prefix: str

    model: Model
    identifier_type: IdentifierType

    kwargs: dict

    get_session: Callable
    get_authentication: Callable

    api_router: APIRouter

    @property
    def delete_url_pattern(self) -> str:
        return "/%s/{id}" % self.prefix

    async def perform_delete(self, id: IdentifierType, session: AsyncSession, *args, **kwargs):
        await session.execute(delete(self.model).where(self.model.id == id))
        await session.commit()

    def register_delete_action(self, *args, **kwargs):
        async def delete(
                request: Request,
                id: self.identifier_type,  # type: ignore
                session: AsyncSession = Depends(self.get_session),
                authentication: Authentication = Depends(self.get_authentication)  # type: ignore
        ):
            logger.info(f"Пришел завпрос на удаление сущности типа {self.model.__name__}")
            try:
                await self.perform_delete(
                    id=id, session=session, request=request, authentication=authentication, *args, **kwargs
                )
            except Exception as e:
                logger.error(f"Ошибка при удалении объекта типа {self.model.__name__}: {e}")
                raise e
            logger.info(f"Cущность типа {self.model.__name__} успешно удалена")

        self.api_router.delete(
            path=self.delete_url_pattern,
            status_code=status.HTTP_204_NO_CONTENT
        )(delete)


class CreateRouterMixin:
    prefix: str

    model: Model
    identifier_type: IdentifierType

    kwargs: dict

    get_session: Callable
    get_authentication: Callable

    create_request_schema: BaseModel.__class__
    create_response_schema: BaseModel.__class__

    api_router: APIRouter

    @property
    def create_url_pattern(self) -> str:
        return "/%s" % self.prefix

    async def perform_create(self, data: BaseModel, session: AsyncSession, *args, **kwargs) -> Model:
        # TODO: Error if entity exists
        instance = self.model(**data.dict())
        session.add(instance)
        await session.commit()
        return instance

    def register_create_action(self, *args, **kwargs):
        if not (self.create_request_schema and self.create_response_schema):
            raise ValueError("create_request_schema and create_response_schema must not be None")

        async def create(
                request: Request,
                data: self.create_request_schema,  # type: ignore
                session: AsyncSession = Depends(self.get_session),
                authentication: Authentication = Depends(self.get_authentication)  # type: ignore
        ) -> self.create_response_schema:  # type: ignore
            logger.info(f"Пришел запрос на создание сущности типа {self.model.__name__}: {data}")
            try:
                response = await self.perform_create(
                    data=data, session=session, request=request, authentication=authentication, *args, **kwargs
                )
            except Exception as e:
                logger.error(f"Ошибка при создании объекта типа {self.model.__name__}: {e}")
                raise e
            logger.info(f"Cущность типа {self.model.__name__} успешно создана: {response}")
            return response

        self.api_router.post(
            path=self.create_url_pattern, response_model=self.create_response_schema,
            status_code=status.HTTP_201_CREATED
        )(create)


class UpdateRouterMixin:
    prefix: str

    model: Model
    identifier_type: IdentifierType

    kwargs: dict

    get_session: Callable
    get_authentication: Callable

    update_request_schema: BaseModel.__class__
    update_response_schema: BaseModel.__class__

    api_router: APIRouter

    @property
    def update_url_pattern(self) -> str:
        return "/%s/{id}" % self.prefix

    async def perform_update(self, id: IdentifierType, data: BaseModel, session: AsyncSession, *args,
                             **kwargs) -> Model:
        query = await session.execute(select(self.model).where(self.model.id == id))
        if instance := query.scalars().first():
            for key, value in data.dict().items():
                setattr(instance, key, value)
            await session.commit()
            return instance
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    def register_update_action(self, *args, **kwargs):
        if not (self.update_request_schema and self.update_response_schema):
            raise ValueError("update_request_schema and update_response_schema must not be None")

        async def update(
                request: Request,
                id: self.identifier_type,  # type: ignore
                data: self.update_request_schema,  # type: ignore
                session: AsyncSession = Depends(self.get_session),
                authentication: Authentication = Depends(self.get_authentication)  # type: ignore
        ) -> self.update_response_schema:  # type: ignore
            logger.info(f"Пришел запрос на обновление сущности типа {self.model.__name__} с id {id}: {data}")
            try:
                response = await self.perform_update(
                    id=id, data=data, session=session, request=request, authentication=authentication, *args, **kwargs
                )
            except Exception as e:
                logger.error(f"Ошибка при обновлении объекта типа {self.model.__name__} с id {id}: {e}")
                raise e
            logger.info(f"Cущность типа {self.model.__name__} с id {id} успешно обновлена: {response}")
            return response

        self.api_router.put(
            path=self.update_url_pattern, response_model=self.update_response_schema,
            status_code=status.HTTP_200_OK
        )(update)


class PartialUpdateRouterMixin:
    prefix: str

    model: Model
    identifier_type: IdentifierType

    kwargs: dict

    get_session: Callable
    get_authentication: Callable

    partial_update_request_schema: BaseModel.__class__
    partial_update_response_schema: BaseModel.__class__

    api_router: APIRouter

    @property
    def partial_update_url_pattern(self) -> str:
        return "/%s/{id}" % self.prefix

    async def perform_partial_update(
            self, id: IdentifierType, data: BaseModel, session: AsyncSession, *args, **kwargs
    ) -> Model:
        query = await session.execute(select(self.model).where(self.model.id == id))
        if instance := query.scalars().first():
            for key, value in data.dict(exclude_none=True, exclude_unset=True).items():
                setattr(instance, key, value)
        await session.commit()
        return instance

    def register_partial_update_action(self, *args, **kwargs):
        if not (self.partial_update_request_schema and self.partial_update_response_schema):
            raise ValueError("partial_update_request_schema and partial_update_response_schema must not be None")

        async def partial_update(
                request: Request,
                id: self.identifier_type,  # type: ignore
                data: self.partial_update_request_schema,  # type: ignore
                session: AsyncSession = Depends(self.get_session),
                authentication: Authentication = Depends(self.get_authentication)  # type: ignore
        ) -> self.partial_update_response_schema:  # type: ignore
            logger.info(f"Пришел запрос на частичное обновление сущности типа {self.model.__name__} с id {id}: {data}")
            try:
                response = await self.perform_partial_update(
                    id=id, data=data, session=session, request=request, authentication=authentication, *args, **kwargs
                )
            except Exception as e:
                logger.error(f"Ошибка при частичное обновлении объекта типа {self.model.__name__} с id {id}: {e}")
                raise e
            logger.info(f"Cущность типа {self.model.__name__} с id {id} успешно частично обновлена: {response}")
            return response

        self.api_router.patch(
            path=self.partial_update_url_pattern,
            response_model=self.partial_update_response_schema,
            status_code=status.HTTP_200_OK
        )(partial_update)


class ModelCRUDRouter(
    RouterGeneric,
    RetrieveRouterMixin,
    ListRouterMixin,
    DeleteRouterMixin,
    CreateRouterMixin,
    UpdateRouterMixin,
    PartialUpdateRouterMixin
):
    pass
