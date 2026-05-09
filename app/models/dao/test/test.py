import datetime

from app.models.dao.base import BaseDAO
from app.models.models import Test

from pydantic import BaseModel, ConfigDict


class TestData(BaseModel):
    test_name: str
    user_id: int = None
    test_time: int
    start_time: datetime.datetime
    is_ended: bool

    model_config = ConfigDict(from_attributes=True)


class TestDao(BaseDAO):
    model = Test
