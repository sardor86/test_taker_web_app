from datetime import datetime

from sqlalchemy import String, ForeignKey, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.database import Base, CloseAnswerEnum, AnswerTypeEnum


class Test(Base):
    test_name: Mapped[str]
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    test_time: Mapped[int] = mapped_column(default=60)
    start_time: Mapped[datetime]
    is_ended: Mapped[bool] = mapped_column(default=False)

    test_attempt: Mapped[list['TestAttempt']] = relationship(
        'test_attempt',
        back_populates='test',
        cascade="all, delete-orphan"
    )

    user: Mapped['User'] = relationship(
        'user',
        back_populates='test',
        uselist=False,
        lazy='joined'
    )

    question: Mapped[list['Question']] = relationship(
        'question',
        back_populates='test',
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f'<Test {self.test_name}>'


class User(Base):
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    lastname: Mapped[str] = mapped_column(String(50))
    city: Mapped[str] = mapped_column(String(50), nullable=False)
    tg_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    is_creator: Mapped[bool] = mapped_column(default=False)

    test_attempt: Mapped['TestAttempt'] = relationship(
        'test_attempt',
        back_populates='user',
        uselist=False,
        lazy='joined',
    )

    test: Mapped['Test'] = relationship(
        'test',
        back_populates='user',
        uselist=False,
        lazy='joined'
    )

    def __repr__(self):
        return f'<User {self.user_id}>'


class TestAttempt(Base):
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    test_id: Mapped[int] = mapped_column(ForeignKey('tests.id'))
    score: Mapped[float] = mapped_column(default=0)
    correct_answers: Mapped[int] = mapped_column(default=0)
    started_at: Mapped[datetime]
    completed_at: Mapped[datetime]

    user: Mapped['User'] = relationship(
        'user',
        back_populates='test_attempt',
        uselist=False,
        lazy='joined',
    )

    user_answer: Mapped[list['UserAnswer']] = relationship(
        "user_answer",
        back_populates="test_attempt",
        cascade="all, delete-orphan"
    )

    test: Mapped['TestAttempt'] = relationship(
        'test',
        back_populates='test_attempt',
    )

    def __repr__(self):
        return f'<TestAttempt user_id={self.user_id} test_id={self.test_id}>'


class Question(Base):
    question_number: Mapped[int] = mapped_column(nullable=False)
    question_type: Mapped[AnswerTypeEnum] = mapped_column(nullable=False)
    correct_answer_id: Mapped[int] = mapped_column(ForeignKey('correctanswers.id'))
    test_id: Mapped[int] = mapped_column(ForeignKey('tests.id'))
    score: Mapped[float] = mapped_column(default=1.0)

    user_answer: Mapped['UserAnswer'] = relationship(
        'user_answer',
        back_populates='question',
        uselist=False,
        lazy='joined',
    )

    test: Mapped['Test'] = relationship(
        'test',
        back_populates='question',
    )

    correct_answer: Mapped['CorrectAnswer'] = relationship(
        'correct_answer',
        back_populates='question',
        uselist=False,
        lazy='joined',
    )

    def __repr__(self):
        return f'<Question question_number={self.question_number} test={self.test_id}>'


class CorrectAnswer(Base):
    answer_type: Mapped[AnswerTypeEnum] = mapped_column(String(200), nullable=False)
    answer: Mapped[str] = mapped_column(nullable=False)

    question: Mapped['Question'] = relationship(
        'question',
        back_populates='correct_answer',
        uselist=False,
        lazy='joined',
    )

    def __repr__(self):
        return f'<CorrectAnswer correct answer={self.answer}>'

class UserAnswer(Base):
    attempt_id: Mapped[int] = mapped_column(ForeignKey('testattempts.id'))
    question_id: Mapped[int] = mapped_column(ForeignKey('questions.id'))
    user_answer: Mapped[str] = mapped_column(String(200), nullable=False)
    is_correct: Mapped[bool] = mapped_column(nullable=False)

    test_attempt: Mapped['TestAttempt'] = relationship(
        'test_attempt',
        back_populates='user_answer',
    )

    question: Mapped['Question'] = relationship(
        'question',
        back_populates='user_answer',
        uselist=False,
        lazy='joined',
    )

    def __repr__(self):
        return f'<UserAnswer attempt_id={self.attempt_id} question={self.answer_id}>'
