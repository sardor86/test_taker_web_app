from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession


class ManagerFabric:
    def __init__(self, async_session_maker: async_sessionmaker[AsyncSession]):
        self.async_session_maker = async_session_maker

    @classmethod
    async def commit(cls, session: AsyncSession):
        try:
            await session.commit()
        except SQLAlchemyError as e:
            await session.rollback()
            raise e
