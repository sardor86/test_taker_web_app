from datetime import datetime
from functools import wraps

from typing import List, Any, Dict
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from pydantic import BaseModel


def connection(method):
    @wraps(method)
    async def wrapper(self, *args, **kwargs):
        async_session_maker = getattr(self, "async_session_maker", None)
        async with async_session_maker() as session:
            try:
                # Явно не открываем транзакции, так как они уже есть в контексте
                return await method(*args, session=session, **kwargs)
            except Exception as e:
                await session.rollback()  # Откатываем сессию при ошибке
                raise e  # Поднимаем исключение дальше
            finally:
                await session.close()  # Закрываем сессию

    return wrapper

class BaseDAO:
    model = None

    def __init__(self, async_session_maker: AsyncSession):
        self.async_session_maker = async_session_maker

    @classmethod
    async def add(cls, session: AsyncSession, **values):
        new_instance = cls.model(**values)
        session.add(new_instance)
        try:
            await session.commit()
        except SQLAlchemyError as e:
            await session.rollback()
            raise e
        return new_instance

    @classmethod
    async def add_many(cls, session: AsyncSession, instances: List[Dict[str, Any]]):
        new_instances = [cls.model(**values) for values in instances]
        session.add_all(new_instances)
        try:
            await session.commit()
        except SQLAlchemyError as e:
            await session.rollback()
            raise e
        return new_instances

    @connection
    async def add(self, data: BaseModel, session):
        instance = self.model(**BaseModel.dict())
        instance.created_at = datetime.now()
        session.add(instance)
        await session.commit()

        return instance
    