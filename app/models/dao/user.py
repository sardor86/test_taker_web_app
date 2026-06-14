from app.models.dao.base import BaseDAO
from app.models.models import User

from pydantic import BaseModel, ConfigDict


class UserData(BaseModel):
    username: str
    lastname: str
    city: str
    tg_user_id: int

    model_config = ConfigDict(from_attributes=True)


class UserDao(BaseDAO):
    model = User
