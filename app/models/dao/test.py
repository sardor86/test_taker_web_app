import datetime

from app.models.dao.base import BaseDAO
from app.models.models import Test

from pydantic import BaseModel

class TestData(BaseModel):
    test_name: str
    user_id: int
    test_time: int
    start_time: datetime.datetime
    is_ended: bool


class TestDAO(BaseDAO):
    model = Test
