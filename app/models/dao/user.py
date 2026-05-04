from app.models.dao.base import BaseDAO
from app.models.models import User

from pydantic import BaseModel

class UserData(BaseModel):
    username: str
    lastname: str
    city: str
    tg_user_id: int
    is_creator: bool


class UserDao(BaseDAO):
    model = User
