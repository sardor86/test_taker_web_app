import datetime
from contextlib import asynccontextmanager
from zoneinfo import ZoneInfo

import pydantic
from aiogram.types import Update
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from redis.asyncio import Redis

from app.config import load_config, PATH
from app.models.dao import (get_test_info,
                            pass_test,
                            add_full_test,
                            check_test_attempt,
                            get_all_users_results,
                            get_users_number)
from app.pydantic_models import SubmitTest, CreateTest
from app.tg_bot.bot import bot, dp, bot_preparation
from app.tg_bot.keyboards.callback import test_controls_keyboard


# app preparation
@asynccontextmanager
async def lifespan(app: FastAPI):
    templates = Jinja2Templates(directory=PATH / 'app/templates')
    app.templates = templates
    app.mount('/app/static', StaticFiles(directory='app/static'), name='static')

    # database preparation
    config = load_config(PATH / '.env')
    db_url = config.get_db_url()
    app.config = config

    engine = create_async_engine(url=db_url)
    async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
    app.async_session_maker = async_session_maker

    # redis preparation
    redis = await Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=0)
    app.redis = redis

    # tg bot preparation
    bot.async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
    bot.redis = redis

    await bot_preparation()

    yield

    await bot.delete_webhook()


app = FastAPI(lifespan=lifespan)

origins = ['*']
app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/")
async def root(request: Request):
    return app.templates.TemplateResponse(name='pass_test.html', context={'request': request})

@app.get("/api/check-test")
async def check_test(test_id: int, user_id: int):
    test = await get_test_info(test_id, async_session_maker=app.async_session_maker, redis=app.redis)

    if not test:
        return {
            'allowed': False,
            'error': 'Test topilmadi'
        }

    if test['is_ended']:
        return {
            'allowed': False,
            'error': 'Test yakunlandi'
        }

    tz_gmt_plus_5 = ZoneInfo("Etc/GMT-5")
    current_time = datetime.datetime.now(tz_gmt_plus_5)

    end_time = datetime.datetime.strptime(test['end_time'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=tz_gmt_plus_5)
    start_time = datetime.datetime.strptime(test['start_time'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=tz_gmt_plus_5)

    if current_time > end_time:
        return {
            'allowed': False,
            'error': 'Test yakunlandi'
        }
    if start_time > current_time:
        return {
            'allowed': False,
            'error': 'Test boshlanmagan'
        }

    test_attempt = await check_test_attempt(test_id, user_id, async_session_maker=app.async_session_maker)

    if test_attempt:
        return {
            'allowed': False,
            'error': 'Siz testdan o\'tib bo\'lgansiz'
        }

    test['allowed'] = True

    return test

@app.post('/api/submit-test')
async def submit_test(user_answers: SubmitTest):
    user_answers.started_at = datetime.datetime.strptime(user_answers.started_at,
                                                         '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=datetime.timezone.utc)
    user_answers.completed_at = datetime.datetime.strptime(user_answers.completed_at,
                                                           '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=datetime.timezone.utc)

    user_and_test_info = await check_test(test_id=user_answers.test_id, user_id=user_answers.user_id)

    if user_and_test_info['allowed']:
        user_results = await pass_test(user_test_data=user_answers, async_session_maker=app.async_session_maker)
        test_info = await get_test_info(test_id=user_answers.test_id, async_session_maker=app.async_session_maker, redis=app.redis)
        completed_time = datetime.datetime.now(ZoneInfo("Etc/GMT-5"))
        message = (f'Ism: {user_results["username"]}\n'
                   f'Familiya: {user_results["lastname"]}\n'
                   f'Viloyat: {user_results["city"]}\n'
                   f'User ID: {user_results["user_id"]}\n'
                   f'To\'g\'ri javoblar: {user_results["correct_answers"]}✅\n'
                   f'Noto\'g\'ri javoblar: {user_results["wrong_answers"]}❌\n'
                   f'Ball: {user_results["score"]}\n'
                   f'Tugatkan vaqti: {completed_time.strftime("%Y-%m-%d %H:%M")}')


        try:
            await bot.send_message(text=f'Sizning natijangiz👇\n\n{message}', chat_id=user_results['user_id'])
            await bot.send_message(text=message, chat_id=test_info['admin_id'])
        except TelegramForbiddenError:
            pass
        except TelegramBadRequest:
            pass
    else:
        message = user_and_test_info['error']

        try:
            await bot.send_message(text=message, chat_id=user_answers.user_id)
        except TelegramForbiddenError:
            pass
        except TelegramBadRequest:
            pass



@app.post("/webhook")
async def webhook(request: Request) -> None:
    update_data = await request.json()
    update = Update(**update_data)
    await dp.feed_update(bot, update)


@app.get("/create/test")
async def root(request: Request):
    return app.templates.TemplateResponse(name='create_test.html', context={'request': request})


@app.get('/api/create/test/check')
async def check_test_name(test_name: str):
    return {
        'allowed': True
    }


@app.post('/api/create/test')
async def create_test(test_data: CreateTest):
    if test_data.user_id is None:
        return {
            'created': False,
            'error': 'User ID talab qilinadi'
        }

    try:
        test_data.start_time = datetime.datetime.strptime(test_data.start_time, '%Y-%m-%d %H:%M:%S.%f')
        test_data.end_time = datetime.datetime.strptime(test_data.end_time, '%Y-%m-%d %H:%M:%S.%f')
    except ValueError as e:
        return {
            'created': False,
            'error': 'Vaqt formati noto\'g\'ri',
        }

    test_id = await add_full_test(test_data=test_data, async_session_maker=app.async_session_maker)

    try:
        await bot.send_message(chat_id=test_data.user_id, text=f'Test yaratildi!\n\n'
                                                               f'Test nomi: {test_data.test_name}\n'
                                                               f'Test kodi: {test_id}\n'
                                                               f'Ajratilgan vaqt: {test_data.test_time}\n'
                                                               f'Ishlash vaqti: {test_data.start_time} dan\n '
                                                               f'{test_data.end_time} gacha\n\n'
                                                               f'Javoblarni yuborish uchun bot: @JahongirAcademyBot\n\n'
                                                               f'Eslatma: Javoblarni faqat @JahongirAcademyBot ga yuboring!',
                               reply_markup=test_controls_keyboard(test_id))
    except TelegramForbiddenError:
        pass
    except TelegramBadRequest:
        pass

    return {
        'created': True,
        'errors': None
    }

class Result(pydantic.BaseModel):
    username: str
    lastname: str
    score: float
    created_at: datetime.datetime

    model_config = pydantic.ConfigDict(from_attributes=True)

class UserResults(pydantic.BaseModel):
    test_name: str
    total_pages: int
    results: list[Result]

@app.get('/api/results/{test_id}')
async def get_test_result(test_id: int, page: int = 1):
    test_info = await get_test_info(test_id=test_id,
                                    async_session_maker=app.async_session_maker,
                                    redis=app.redis)
    results = await get_all_users_results(test_id=test_id,
                                          page=page,
                                          async_session_maker=app.async_session_maker)
    total_number = await get_users_number(test_id=test_id,
                                          async_session_maker=app.async_session_maker)

    total_page = (total_number + 99) // 100

    return UserResults(
        test_name=test_info['test_name'],
        total_pages=total_page,
        results=results
    )


@app.get('/results/{test_id}')
async def get_test_result(request: Request):
    return app.templates.TemplateResponse(name='results.html', context={'request': request})
