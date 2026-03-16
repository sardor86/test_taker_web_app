import copy
from io import BytesIO

from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from aiogram.types import CallbackQuery, BufferedInputFile
from redis import Redis
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from fpdf import FPDF
from sqlalchemy.ext.asyncio import AsyncSession

from reportlab.pdfgen import canvas
from PyPDF2 import PdfReader, PdfWriter


from app.models.dao import (stop_testing,
                            get_all_users_results,
                            get_user_data,
                            get_test_info, get_test_answers,
                            add_new_admin)
from app.config import PATH

admin_router = Router()


class Certificate:
    def __init__(self):
        font_path = PATH / 'app/tg_bot/certificates/DejaVuSans-Bold.ttf'
        pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', font_path))

        self.CERTIFICATE_LIST = [
            PdfReader(open(PATH / 'app/tg_bot/certificates/0.pdf', 'rb')).pages[0],
            PdfReader(open(PATH / 'app/tg_bot/certificates/1.pdf', 'rb')).pages[0],
            PdfReader(open(PATH / 'app/tg_bot/certificates/2.pdf', 'rb')).pages[0],
            PdfReader(open(PATH / 'app/tg_bot/certificates/3.pdf', 'rb')).pages[0],
        ]
        self.PAGE_SIZE_BY_X = 595
        self.PAGE_SIZE_BY_Y = 842

        self.FONT_NAME = 'DejaVuSans-Bold'
        self.FONT_SIZE = 28
        self.TEXT_PLACE_Y = 410
        self.TEXT_PLACE_X = None

        self.certificate_number = None
        self.full_name = None

        self.overlay = BytesIO()
        self.certificate = BytesIO()
        self.canvas = canvas.Canvas(self.overlay, pagesize=(self.PAGE_SIZE_BY_X, self.PAGE_SIZE_BY_Y))
        self.overlay_pdf = None
        self.writer = PdfWriter()
        self.result_file = None

    def set_certificate_type_by_place(self, place: int):
        if place <= 2:
            self.certificate_number = place
        else:
            self.certificate_number = 3

    def set_text_place_x(self):
        text_width = pdfmetrics.stringWidth(self.full_name, self.FONT_NAME, self.FONT_SIZE)
        self.TEXT_PLACE_X = (549 - text_width) / 2

    def prepare_text_of_full_name(self):
        self.set_text_place_x()
        self.canvas.setFont(self.FONT_NAME, self.FONT_SIZE)
        self.canvas.drawString(self.TEXT_PLACE_X, self.TEXT_PLACE_Y, self.full_name)

    def prepare_overlay_for_pdf_file(self):
        self.overlay.seek(0)
        self.overlay_pdf = PdfReader(self.overlay)

    def prepare_certificate_file(self):
        page = copy.copy(self.CERTIFICATE_LIST[self.certificate_number])
        page.merge_page(self.overlay_pdf.pages[0])
        self.writer.add_page(page)

    def write_certificate_file(self):
        self.writer.write(self.certificate)
        self.result_file = BufferedInputFile(self.certificate.getvalue(), filename='certificate.pdf')

    def prepare_certificate(self):
        self.prepare_text_of_full_name()
        self.canvas.save()
        self.prepare_overlay_for_pdf_file()
        self.prepare_certificate_file()


class PDFResultsTable:
    def __init__(self):
        self.COLUMN_WIDTH = 40
        self.ROW_HEIGHT = 10
        self.BORDER = 1

        self.pdf = FPDF()

        self.session = None
        self.data = None
        self.file_name = None
        self.result_file = None

    def set_font_for_column(self):
        self.pdf.set_font('Arial', 'B', 16)

    def set_font_for_data(self):
        self.pdf.set_font('Arial', '', 12)

    def create_columns_for_table(self):
        self.pdf.cell(self.COLUMN_WIDTH, self.ROW_HEIGHT, 'First Name', self.BORDER)
        self.pdf.cell(self.COLUMN_WIDTH, self.ROW_HEIGHT, 'Last Name', self.BORDER)
        self.pdf.cell(self.COLUMN_WIDTH, self.ROW_HEIGHT, 'Score', self.BORDER)
        self.pdf.ln(10)

    async def draw_one_line_of_data(self, attempt):
        user_data = await get_user_data(user_id=attempt.user_id, async_session_maker=self.session)
        self.pdf.cell(self.COLUMN_WIDTH, self.ROW_HEIGHT, user_data.username, self.BORDER)
        self.pdf.cell(self.COLUMN_WIDTH, self.ROW_HEIGHT, user_data.lastname, self.BORDER)
        self.pdf.cell(self.COLUMN_WIDTH, self.ROW_HEIGHT, str(attempt.score), self.BORDER)
        self.pdf.ln(10)

    async def draw_all_user_data(self):
        for user in self.data:
            await self.draw_one_line_of_data(user)

    def prepare_pdf_output(self):
        self.result_file = BufferedInputFile(self.pdf.output('S').encode('latin-1'), filename='results.pdf')

    async def create_pdf_table(self):
        self.pdf.add_page()
        self.set_font_for_column()
        self.create_columns_for_table()
        self.set_font_for_data()
        await self.draw_all_user_data()
        self.prepare_pdf_output()


async def test_results_message_parts(test_id: int, session: AsyncSession, redis: Redis) -> list:
    test_info = await get_test_info(test_id, async_session_maker=session, redis=redis)

    message_parts = ['Test natijalari:\n\n'
                     f'Test nomi: {test_info["test_name"]}\n'
                     f'Test kodi: {test_id}\n\n'
                     '\n\nToʻgʻri javoblar: ']

    answers = await get_test_answers(test_id, async_session_maker=session)
    per_row = 6
    rows = []
    for i in range(0, len(answers), per_row):
        part = answers[i:i + per_row]
        row = []
        for j, ans in enumerate(part, start=i + 1):
            row.append(f"{j}.{ans.correct_answer}".ljust(10))
        rows.append("".join(row))

    table = "\n".join(rows)
    message_answer_table = f"```\n{table}\n```"
    message_parts.append(message_answer_table)

    message_parts.append('\nTestda ishtirok etgan barchaga rahmat😊')
    return message_parts


async def send_certificates(test_id, bot: Bot, session: AsyncSession, redis: Redis):
    results = (await get_all_users_results(test_id,
                                           async_session_maker=session))
    test_info = await get_test_info(test_id, async_session_maker=session, redis=redis)
    certificate = Certificate()

    for i, attempt in enumerate(results):
        user_data = await get_user_data(user_id=attempt.user_id, async_session_maker=session)
        full_name = f'{user_data.lastname} {user_data.username}'

        certificate.full_name = full_name
        certificate.set_certificate_type_by_place(i)
        certificate.prepare_certificate()
        certificate_file = certificate.result_file

        try:
            await bot.send_message(chat_id=attempt.tg_user_id,
                                   text=f'Testda qatnashganingiz uchun rahmat,\n'
                                        f'Natijalar:\n'
                                        f'Test nomi: {test_info["test_name"]}\n'
                                        f'Ball: {attempt.score}\n'
                                        f'O\'rningiz: {i + 1}')
        except TelegramForbiddenError:
            pass
        except TelegramBadRequest:
            pass

        try:
            await bot.send_document(chat_id=attempt.tg_user_id, document=certificate_file)
        except TelegramForbiddenError:
            pass
        except TelegramBadRequest:
            pass


async def send_results(test_id, callback: CallbackQuery, session: AsyncSession):
    results = await get_all_users_results(test_id, async_session_maker=session)
    results_table = PDFResultsTable()
    results_table.session = session
    results_table.file_name = 'results.pdf'
    results_table.data = results
    results_table.prepare_pdf_output()

    results_file = results_table.result_file

    try:
        await callback.bot.send_document(chat_id=callback.message.chat.id, document=results_file)
    except TelegramForbiddenError:
        pass
    except TelegramBadRequest:
        pass

@admin_router.callback_query(F.data.split('::')[0] == 'stop_test')
async def stop_test(callback: CallbackQuery) -> None:
    await stop_testing(test_id=callback.data.split('::')[-1],
                    async_session_maker=callback.bot.async_session_maker,
                    redis=callback.bot.redis)
    try:
        await callback.message.reply('Test yakunlandi!')
    except TelegramForbiddenError:
        pass
    except TelegramBadRequest:
        pass

    test_id = int(callback.data.split('::')[-1])
    message_parts = await test_results_message_parts(test_id=test_id,
                                                     session=callback.bot.async_session_maker,
                                                     redis=callback.bot.redis,)

    try:
        await callback.message.reply(text='\n'.join(message_parts))
    except TelegramForbiddenError:
        pass
    except TelegramBadRequest:
        pass
    await send_certificates(test_id=test_id,
                            session=callback.bot.async_session_maker,
                            redis=callback.bot.redis,
                            bot=callback.bot)
    await send_results(test_id=test_id, callback=callback, session=callback.bot.async_session_maker)


@admin_router.callback_query(F.data.split('::')[0] == 'get_results_test')
async def get_results_test(callback: CallbackQuery) -> None:
    test_id = int(callback.data.split('::')[-1])
    message_parts = await test_results_message_parts(test_id=test_id,
                                                     session=callback.bot.async_session_maker,
                                                     redis=callback.bot.redis)
    try:
        await callback.message.reply(text='\n'.join(message_parts))
    except TelegramForbiddenError:
        pass
    except TelegramBadRequest:
        pass
    await send_results(test_id=test_id, callback=callback, session=callback.bot.async_session_maker)


@admin_router.callback_query(F.data.split('::')[0] == 'allow_admin')
async def allow_admin(callback: CallbackQuery) -> None:
    user_id = int(callback.data.split('::')[-1])

    await add_new_admin(user_id=user_id, async_session_maker=callback.bot.async_session_maker)

    try:
        await callback.bot.send_message(chat_id=callback.bot.config.ADMIN_ID,
                                        text=f'Siz {user_id} id bilan odamga test yaratishga ruhsat berdingiz')
        await callback.bot.send_message(chat_id=user_id, text='Sizga test yaratishga ruhsat berildi')
    except TelegramForbiddenError:
        pass
    except TelegramBadRequest:
        pass
