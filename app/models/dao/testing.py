import asyncio

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.models.dao import QuestionData, TestData, UserData
from app.models.test_manager import TestManager, TestAggregateData

from app.config import load_config, PATH


async def create_test():
    test_data = {
        'test_name': 'test2',
        'test_time': '60',
        'start_time': '2026-05-03 14:00',
        'is_ended': False
    }

    user_data = {
        'username': 'Sardor',
        'lastname': 'Shavkatov',
        'city': 'Tashkent',
        'tg_user_id': '12345567',
        'is_creator': True
    }

    question_data = [
        {
            'question_number': '1',
            'question_type': 'close',
            'score': 1,
            'answer': 'B'
        },
        {
            'question_number': '1',
            'question_type': 'close',
            'score': 1,
            'answer': 'B'
        },
        {
            'question_number': '1',
            'question_type': 'close',
            'score': 1,
            'answer': 'B'
        },
        {
            'question_number': '1',
            'question_type': 'close',
            'score': 1,
            'answer': 'B'
        },
        {
            'question_number': '1',
            'question_type': 'close',
            'score': 1,
            'answer': 'B'
        },
        {
            'question_number': '1',
            'question_type': 'close',
            'score': 1,
            'answer': 'B'
        }
    ]

    create_test_data = TestAggregateData(
        user=UserData(**user_data),
        test=TestData(**test_data),
        question=[QuestionData(**question) for question in question_data]
    )

    config = load_config(PATH / '.env')

    engine = create_async_engine(url=config.get_db_url(), echo=True)
    async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

    test_manager = TestManager(async_session_maker)
    await test_manager.create_test(test_create_data=create_test_data)

async def get_test(test_id: int):
    config = load_config(PATH / '.env')

    engine = create_async_engine(url=config.get_db_url(), echo=True)
    async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

    test_manager = TestManager(async_session_maker)

    test_info = await test_manager.get_test_info(test_id=test_id)
    print(test_info.dict())

asyncio.run(create_test())
asyncio.run(get_test(2))
