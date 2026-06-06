import json

from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dao.dao import TestDAO, TestAttemptDAO, UserDAO, AnswerDAO, TestCreatorDAO
from app.models.database import connection


@connection
async def get_test_info(test_id: int, session: AsyncSession, redis: Redis = None) -> dict | None:
    test_data = await redis.get(str(test_id))
    if test_data is None:
        test = await TestDAO().get_test_info_by_id(test_id=test_id, session=session)
        if test is not None:
            test_new_data = {
                'minutes': test.test_time,
                'open_questions': test.open_questions,
                'close_questions': test.close_questions,
                'test_name': test.test_name,
                'test_id': test.id,
                'start_time': test.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                'end_time': test.end_time.strftime("%Y-%m-%d %H:%M:%S"),
                'admin_id': test.user_id,
                'is_ended': test.is_ended,
            }

            await redis.set(str(test_id), json.dumps(test_new_data), ex=259200)

            return test_new_data
        return None

    return json.loads(test_data)

@connection
async def check_test_attempt(test_id: int, user_id: int, session: AsyncSession) -> bool:
    attempt_data = not (await TestAttemptDAO.check_test_attempts(test_id=test_id, user_id=user_id, session=session))
    return not attempt_data

@connection
async def get_all_results(user_id: int, session: AsyncSession):
    test = await TestAttemptDAO.get_all_results(user_id=user_id, session=session)
    return test

@connection
async def get_user_answers(user_attempt: int, session: AsyncSession):
    test = await TestAttemptDAO.get_user_answers(user_attempt=user_attempt, session=session)
    return test

@connection
async def get_all_test_attempts(user_id: int, session: AsyncSession):
    test = await TestAttemptDAO.get_all_test_attempts(user_id=user_id, session=session)
    return test

@connection
async def get_all_users_results(test_id: int, session: AsyncSession, page: int = 1):
    results = await TestDAO.get_all_results(test_id=test_id, session=session, page=page)
    return results

@connection
async def get_all_test_results(test_id: int, session: AsyncSession):
    results = await TestDAO.get_all_test_results(test_id=test_id, session=session)
    return results

@connection
async def get_users_number(test_id: int, session: AsyncSession):
    result = await TestDAO.get_users_number(test_id=test_id, session=session)
    return result


@connection
async def get_user_data(user_id: int, session: AsyncSession):
    result = await UserDAO.get_user_data_by_id(user_id=user_id, session=session)
    return result


@connection
async def get_test_answers(test_id: int, session: AsyncSession):
    result = await AnswerDAO.get_all_answers(test_id=test_id, session=session)
    return result


@connection
async def check_admin(user_id: int, session: AsyncSession) -> bool:
    result = await TestCreatorDAO.check_is_admin(session=session, user_id=user_id)
    return result
