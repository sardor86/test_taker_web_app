from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dao import test, question, correct_answer
from app.models.dao.test import TestDAO


class TestCreateData(BaseModel):
    test: test.TestData
    question: list[question.QuestionData]
    answer: list[correct_answer.CorrectAnswerData]


class TestManager:
    def __init__(self, async_session_maker: AsyncSession):
        self.async_session_maker = async_session_maker

    def create_test(self, test_create_data: TestCreateData) -> Test:
        test_dao = test.Test(async_session_maker=self.async_session_maker)
        test.add()