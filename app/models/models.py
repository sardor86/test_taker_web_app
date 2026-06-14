from datetime import datetime

from sqlalchemy import String, ForeignKey, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.database import Base, AnswerTypeEnum


class Test(Base):
    test_name: Mapped[str]
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    test_time: Mapped[int] = mapped_column(default=60)
    start_time: Mapped[datetime]
    is_ended: Mapped[bool] = mapped_column(default=False)

    test_attempt: Mapped[list['TestAttempt']] = relationship(
        'TestAttempt',
        back_populates='test',
        uselist=True
    )

    user: Mapped['User'] = relationship(
        'User',
        back_populates='test',
        uselist=False,
        lazy='joined'
    )

    question: Mapped[list['Question']] = relationship(
        'Question',
        back_populates='test',
        cascade='all, delete-orphan',
        uselist=True,
        lazy='joined'
    )

    def __repr__(self):
        return f'<Test {self.test_name}>'


class User(Base):
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    lastname: Mapped[str] = mapped_column(String(50))
    city: Mapped[str] = mapped_column(String(50), nullable=False)
    tg_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    test_attempt: Mapped['TestAttempt'] = relationship(
        'TestAttempt',
        back_populates='user',
        cascade='all, delete-orphan',
        uselist=True,
        lazy='joined',
    )

    test: Mapped['Test'] = relationship(
        'Test',
        back_populates='user',
        cascade='all, delete-orphan',
        uselist=True,
        lazy='joined'
    )

    def __repr__(self):
        return f'<User {self.tg_user_id}>'


class TestAttempt(Base):
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    test_id: Mapped[int] = mapped_column(ForeignKey('tests.id'))
    score: Mapped[float] = mapped_column(default=0)
    correct_answers: Mapped[int] = mapped_column(default=0)
    started_at: Mapped[datetime]
    completed_at: Mapped[datetime]

    user: Mapped['User'] = relationship(
        'User',
        back_populates='test_attempt',
        uselist=False,
        lazy='joined',
    )

    user_answer: Mapped[list['UserAnswer']] = relationship(
        'UserAnswer',
        back_populates="test_attempt",
        cascade="all, delete-orphan",
        uselist=True,
        lazy='joined',
    )

    test: Mapped['Test'] = relationship(
        'Test',
        back_populates='test_attempt',
        uselist=False
    )

    def __repr__(self):
        return f'<TestAttempt user_id={self.user_id} test_id={self.test_id}>'


class Question(Base):
    question_number: Mapped[int] = mapped_column(nullable=False)
    question_type: Mapped[AnswerTypeEnum] = mapped_column(nullable=False)
    answer: Mapped[str] = mapped_column(nullable=False)
    test_id: Mapped[int] = mapped_column(ForeignKey('tests.id'))
    score: Mapped[float] = mapped_column(default=1.0)

    user_answer: Mapped['UserAnswer'] = relationship(
        'UserAnswer',
        back_populates='question',
        uselist=False,
        lazy='joined',
    )

    test: Mapped['Test'] = relationship(
        'app.models.models.Test',
        back_populates='question',
    )

    def __repr__(self):
        return f'<Question question_number={self.question_number} test={self.test_id}>'


class UserAnswer(Base):
    attempt_id: Mapped[int] = mapped_column(ForeignKey('testattempts.id'))
    question_id: Mapped[int] = mapped_column(ForeignKey('questions.id'))
    user_answer: Mapped[str] = mapped_column(String(200), nullable=False)
    is_correct: Mapped[bool] = mapped_column(nullable=False)

    test_attempt: Mapped['TestAttempt'] = relationship(
        'TestAttempt',
        back_populates='user_answer',
    )

    question: Mapped['Question'] = relationship(
        'Question',
        back_populates='user_answer',
        uselist=False,
        lazy='joined',
    )

    def __repr__(self):
        return f'<UserAnswer attempt_id={self.attempt_id} question={self.question_id}>'
