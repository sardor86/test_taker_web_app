from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import TestAttempt
from app.models.dao.base import connection
from app.models.manager import ManagerFabric
from models.dao import UserData, UserDao
from test_attempt import TestAttemptData, TestAttemptDao
from test_attempt import UserAnswerData, UserAnswerDao


class AttemptAggregateData(BaseModel):
    user: UserData
    test_attempt: TestAttemptData
    user_answers: list[UserAnswerData]


class TestAttemptManager(ManagerFabric):
    test_attempt = None

    async def add_and_set_test_attempt(self, test_attempt: TestAttemptData, session: AsyncSession):
        self.test_attempt = await TestAttemptDao().add(**test_attempt.model_dump(), session=session)

    async def add_and_set_user(self, user: UserData, session: AsyncSession):
        user = await UserDao().add(**user.model_dump(), session=session)
        self.test_attempt.user = user

    async def add_and_set_user_answer(self, user_answers: list[UserAnswerData], session: AsyncSession):
        user_answers = await UserAnswerDao().add_many(user_answers, session=session)
        self.test_attempt.user_answers = user_answers

    @connection
    async def create_test_attempt(self, user_test_attempt_data: AttemptAggregateData, session: AsyncSession):
        await self.add_and_set_test_attempt(user_test_attempt_data.test_attempt, session)
        await self.add_and_set_user_answer(user_test_attempt_data.user_answers, session)
        await self.add_and_set_user_answer(user_test_attempt_data.user_answers, session)

        return self.test_attempt

    @classmethod
    async def get_all_attempts_from_db(cls, user_id: int, session: AsyncSession):
        stmp = select(TestAttempt).where(TestAttempt.user_id == user_id)
        attempt_info = (await session.execute(stmp)).scalars().all()
        return attempt_info

    @classmethod
    def get_attempt_aggregate(cls, attempt_info):
        attempt_aggregate_data = AttemptAggregateData(
            user=attempt_info.user,
            test_attempt=attempt_info,
            user_answers=attempt_info.user_answers,
        )
        return attempt_aggregate_data

    @connection
    async def get_test_attempt(self, user_id: int, session: AsyncSession):
        attempts_info = await self.get_all_attempts_from_db(user_id, session)
        return [self.get_attempt_aggregate(attempt) for attempt in attempts_info]
