from app.models.dao.base import BaseDAO
from app.models.models import Question
from app.models.models import AnswerTypeEnum

from pydantic import BaseModel


class QuestionData(BaseModel):
    question_number: int
    question_type: AnswerTypeEnum
    correct_answer_id: int
    test_id: int
    score: float


class QuestionDao(BaseDAO):
    model = Question

