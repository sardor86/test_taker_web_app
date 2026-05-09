from app.models.dao.base import BaseDAO
from app.models.models import Question
from app.models.models import AnswerTypeEnum

from pydantic import BaseModel, ConfigDict


class QuestionData(BaseModel):
    question_number: int
    question_type: AnswerTypeEnum
    answer: str
    test_id: int = None
    score: float

    model_config = ConfigDict(from_attributes=True)


class QuestionDao(BaseDAO):
    model = Question

