from app.models.dao.base import BaseDAO
from app.models.models import CorrectAnswer
from app.models.models import AnswerTypeEnum

from pydantic import BaseModel


class CorrectAnswerData(BaseModel):
    answer_type: AnswerTypeEnum
    answer: str

class CorrectAnswerDao(BaseDAO):
    model = CorrectAnswer

