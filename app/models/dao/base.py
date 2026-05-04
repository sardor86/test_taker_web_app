from functools import wraps

from typing import List, Any, Dict
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


def connection(method):
    @wraps(method)
    async def wrapper(self, *args, **kwargs):
        async_session_maker = getattr(self, "async_session_maker", None)
        async with async_session_maker() as session:
            try:
                # Явно не открываем транзакции, так как они уже есть в контексте
                return await method(self, *args, session=session, **kwargs)
            except Exception as e:
                await session.rollback()  # Откатываем сессию при ошибке
                raise e  # Поднимаем исключение дальше
            finally:
                await session.close()  # Закрываем сессию

    return wrapper

class BaseDAO:
    model = None

    async def add(self, session: AsyncSession, **values):
        new_instance = self.model(**values)
        session.add(new_instance)
        return new_instance

    async def add_many(self, session: AsyncSession, instances: List[Dict[str, Any]]):
        new_instances = [self.model(**values) for values in instances]
        session.add_all(new_instances)
        return new_instances

    @classmethod
    async def commit(cls, session: AsyncSession):
        try:
            await session.commit()
        except SQLAlchemyError as e:
            await session.rollback()
            raise e
    