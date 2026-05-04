from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.dao.base import connection
from app.models.manager import ManagerFabric
from app.models.dao import TestData, TestDao
from app.models.dao import QuestionData, QuestionDao
from app.models.dao import CorrectAnswerData, CorrectAnswerDao
from app.models.dao import UserData, UserDao
from app.models.models import Question


class QuestionAnswerData(BaseModel):
    question: QuestionData
    answer: CorrectAnswerData


class TestCreateData(BaseModel):
    user: UserData
    test: TestData
    question_answer: list[QuestionAnswerData]


class TestManager(ManagerFabric):
    def __init__(self, async_session_maker: async_sessionmaker[AsyncSession]):
        self.async_session_maker = async_session_maker
        self.test = None

    async def attach_question_to_test(self, question: Question):
        self.test.question.append(question)

    @classmethod
    async def create_question_with_answer(cls, data: QuestionAnswerData, session: AsyncSession):
        correct_answer = await CorrectAnswerDao().add(**data.answer.model_dump(), session=session)
        question = await QuestionDao().add(**data.question.model_dump(), session=session)

        question.correct_answer = correct_answer
        return question

    async def add_full_question(self, data: QuestionAnswerData, session: AsyncSession):
        question = await self.create_question_with_answer(data, session)
        await self.attach_question_to_test(question)

    async def add_and_set_all_question_answer(self, question_answer_list: list[QuestionAnswerData], session: AsyncSession):
        for question_answer in question_answer_list:
            await self.add_full_question(question_answer, session)

    async def add_and_set_test(self, test: TestData, session: AsyncSession):
        test = await TestDao().add(**test.model_dump(), session=session)
        self.test = test

    async def add_and_set_user(self, user: UserData, session: AsyncSession):
        user = await UserDao().add(**user.model_dump(), session=session)
        self.test.user = user

    @connection
    async def create_test(self, test_create_data: TestCreateData, session: AsyncSession) -> int:
        await self.add_and_set_test(test_create_data.test, session)
        await self.add_and_set_user(test_create_data.user, session)
        await self.add_and_set_all_question_answer(test_create_data.question_answer, session)

        await self.commit(session)
        return self.test.id
