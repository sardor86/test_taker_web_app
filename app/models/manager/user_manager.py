from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.dao.base import connection
from app.models.manager import ManagerFabric
from app.models.dao import UserData, UserDao
from app.models import User


class UserManager(ManagerFabric):
    @classmethod
    async def get_user_by_tg_id(cls, tg_user_id: int, session: AsyncSession) -> User | None:
        stmp = select(User).where(User.tg_user_id == tg_user_id)
        return (await session.execute(stmp)).scalars().first()

    @connection
    async def create_user(self, user_data: UserData, session: AsyncSession) -> User:
        user = await self.get_user_by_tg_id(user_data.tg_user_id, session)
        if not user is None:
            return user
        return await UserDao().add(**user_data.model_dump(), session=session)
