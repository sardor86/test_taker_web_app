from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from models.dao.base import BaseDAO
from models.models import UserAnswer


class UserAnswerData(BaseModel):
    attempt_id: int = None
    question_id: int
    user_answer: str
    is_correct: bool


class UserAnswerDao(BaseDAO):
    model: UserAnswer

    async def add(self, session: AsyncSession, **values):
        pass
