from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import TestAttempt, User
from app.models.dao.base import connection
from app.models.manager import ManagerFabric
from test_attempt import TestAttemptData, TestAttemptDao
from test_attempt import UserAnswerData, UserAnswerDao


class AttemptAggregateData(BaseModel):
    user: User
    test_attempt: TestAttemptData
    user_answers: list[UserAnswerData]


class TestAttemptManager(ManagerFabric):
    test_attempt = None

    @connection
    async def create_test_attempt(self, test_attempt_data: AttemptAggregateData, session: AsyncSession):
        self.test_attempt = await TestAttemptDao().add(**test_attempt_data.test_attempt.model_dump(), session=session)
        self.test_attempt.user = test_attempt_data.user
        user_answers = await UserAnswerDao().add_many(test_attempt_data.user_answers, session=session)
        self.test_attempt.user_answers = user_answers

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
