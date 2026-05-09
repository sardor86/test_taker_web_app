import datetime

from app.models.dao.base import BaseDAO
from app.models.models import Test

from pydantic import BaseModel

class TestAttemptData(BaseModel):
    user_id: int = None
    test_id: int = None
    score: int
    correct_answers: int
    started_at: datetime.datetime
    completed_at: datetime.datetime


class TestAttemptDao(BaseDAO):
    model = Test
