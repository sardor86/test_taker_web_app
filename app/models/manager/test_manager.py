from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.dao.base import connection
from app.models.manager import ManagerFabric
from app.models.dao.test import TestData, TestDao
from app.models.dao.test import QuestionData, QuestionDao
from app.models.models import Test, TestAttempt, User
from models.manager.test_attempt_manager import AttemptAggregateData, TestAttemptManager


class TestAggregateData(BaseModel):
    user: User
    test: TestData
    question: list[QuestionData]


class TestManager(ManagerFabric):
    test = None

    @connection
    async def create_test(self, test_create_data: TestAggregateData, session: AsyncSession) -> int:
        self.test = await TestDao().add(**test_create_data.test.model_dump(), session=session)
        self.test.user = test_create_data.user
        self.test.question = await QuestionDao().add_many(test_create_data.question, session=session)

        await self.commit(session)
        return self.test.id

    @classmethod
    async def get_test_from_db(cls, test_id: int, session: AsyncSession):
        stmp = select(Test).where(Test.id == test_id)
        test_info = (await session.execute(stmp)).scalars().first()
        return test_info

    @classmethod
    def get_test_aggregate(cls, test_info: Test):
        test_aggregate_data = TestAggregateData(
            test=TestData.from_orm(test_info),
            user=test_info.user,
            question=[QuestionData.from_orm(question) for question in test_info.question]
        )
        return test_aggregate_data

    @connection
    async def get_test_info(self, test_id: int, session: AsyncSession) -> TestAggregateData:
        test_info = await self.get_test_from_db(test_id, session)
        test_aggregate_data = self.get_test_aggregate(test_info)
        return test_aggregate_data

    @classmethod
    async def get_test_attempts_from_db(cls, test_id: int, session: AsyncSession):
        stmp = select(TestAttempt).where(TestAttempt.test_id == test_id).order_by(TestAttempt.score.desc())
        return (await session.execute(stmp)).scalars().all()

    @connection
    async def get_test_results(self, test_id: int, session: AsyncSession) -> list[AttemptAggregateData]:
        attempt_info = await self.get_test_attempts_from_db(test_id, session)
        return [TestAttemptManager.get_attempt_aggregate(attempt) for attempt in attempt_info]
