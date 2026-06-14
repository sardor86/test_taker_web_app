import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel as PydanticBaseModel
from typing import List


# ─── Minimal stubs so we can import BaseDAO without a real DB ───────────────

class FakeModel:
    """Minimal SQLAlchemy-like model stub."""

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


# ─── Inline BaseDAO (copy of dao/base.py logic) ─────────────────────────────
# If your project is installed as a package you can do:
#   from app.models.dao.base import BaseDAO, connection
# and remove the inline version below.

from functools import wraps
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dao.base import BaseDAO, connection


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_session():
    """Async-compatible mock of an SQLAlchemy AsyncSession."""
    session = AsyncMock(spec=AsyncSession)
    session.add = MagicMock()          # add() is sync in SQLAlchemy
    session.add_all = MagicMock()      # add_all() is sync in SQLAlchemy
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def dao():
    """BaseDAO instance with FakeModel attached."""
    d = BaseDAO()
    d.model = FakeModel
    return d


def make_session_maker(session):
    """Return an async context-manager factory that yields *session*."""
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=session)
    cm.__aexit__ = AsyncMock(return_value=False)
    maker = MagicMock(return_value=cm)
    return maker


# ─── Tests: BaseDAO.add ──────────────────────────────────────────────────────

class TestBaseDAOAdd:

    @pytest.mark.asyncio
    async def test_add_creates_instance_with_correct_values(self, dao, mock_session):
        result = await dao.add(mock_session, name="Alice", age=30)

        assert isinstance(result, FakeModel)
        assert result.name == "Alice"
        assert result.age == 30

    @pytest.mark.asyncio
    async def test_add_calls_session_add(self, dao, mock_session):
        result = await dao.add(mock_session, name="Bob")

        mock_session.add.assert_called_once_with(result)

    @pytest.mark.asyncio
    async def test_add_with_no_values(self, dao, mock_session):
        result = await dao.add(mock_session)

        assert isinstance(result, FakeModel)
        mock_session.add.assert_called_once()


# ─── Tests: BaseDAO.add_many ─────────────────────────────────────────────────

class SampleSchema(PydanticBaseModel):
    name: str
    age: int


class TestBaseDAOAddMany:

    @pytest.mark.asyncio
    async def test_add_many_returns_correct_count(self, dao, mock_session):
        items = [SampleSchema(name="A", age=1), SampleSchema(name="B", age=2)]
        result = await dao.add_many(items, mock_session)

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_add_many_maps_fields_correctly(self, dao, mock_session):
        items = [SampleSchema(name="Alice", age=25)]
        result = await dao.add_many(items, mock_session)

        assert result[0].name == "Alice"
        assert result[0].age == 25

    @pytest.mark.asyncio
    async def test_add_many_calls_session_add_all(self, dao, mock_session):
        items = [SampleSchema(name="X", age=10), SampleSchema(name="Y", age=20)]
        result = await dao.add_many(items, mock_session)

        mock_session.add_all.assert_called_once_with(result)

    @pytest.mark.asyncio
    async def test_add_many_empty_list(self, dao, mock_session):
        result = await dao.add_many([], mock_session)

        assert result == []
        mock_session.add_all.assert_called_once_with([])


# ─── Tests: BaseDAO.commit ────────────────────────────────────────────────────

class TestBaseDAOCommit:

    @pytest.mark.asyncio
    async def test_commit_calls_session_commit(self, mock_session):
        await BaseDAO.commit(mock_session)

        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_commit_rolls_back_on_sqlalchemy_error(self, mock_session):
        mock_session.commit.side_effect = SQLAlchemyError("DB failure")

        with pytest.raises(SQLAlchemyError):
            await BaseDAO.commit(mock_session)

        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_commit_re_raises_original_exception(self, mock_session):
        original_error = SQLAlchemyError("unique constraint violated")
        mock_session.commit.side_effect = original_error

        with pytest.raises(SQLAlchemyError, match="unique constraint violated"):
            await BaseDAO.commit(mock_session)


# ─── Tests: connection decorator ─────────────────────────────────────────────

class TestConnectionDecorator:

    @pytest.mark.asyncio
    async def test_injects_session_into_method(self, mock_session):
        received = {}

        class MyDAO:
            async_session_maker = make_session_maker(mock_session)

            @connection
            async def my_method(self, session=None, **kwargs):
                received["session"] = session
                return "ok"

        result = await MyDAO().my_method()

        assert result == "ok"
        assert received["session"] is mock_session

    @pytest.mark.asyncio
    async def test_closes_session_on_success(self, mock_session):
        class MyDAO:
            async_session_maker = make_session_maker(mock_session)

            @connection
            async def my_method(self, session=None):
                return "done"

        await MyDAO().my_method()

        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_rolls_back_on_exception(self, mock_session):
        class MyDAO:
            async_session_maker = make_session_maker(mock_session)

            @connection
            async def my_method(self, session=None):
                raise ValueError("something went wrong")

        with pytest.raises(ValueError, match="something went wrong"):
            await MyDAO().my_method()

        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_closes_session_even_after_exception(self, mock_session):
        class MyDAO:
            async_session_maker = make_session_maker(mock_session)

            @connection
            async def my_method(self, session=None):
                raise RuntimeError("boom")

        with pytest.raises(RuntimeError):
            await MyDAO().my_method()

        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_passes_extra_kwargs_through(self, mock_session):
        received = {}

        class MyDAO:
            async_session_maker = make_session_maker(mock_session)

            @connection
            async def my_method(self, user_id=None, session=None):
                received["user_id"] = user_id
                return user_id

        result = await MyDAO().my_method(user_id=42)

        assert result == 42
        assert received["user_id"] == 42

    @pytest.mark.asyncio
    async def test_does_not_rollback_on_success(self, mock_session):
        class MyDAO:
            async_session_maker = make_session_maker(mock_session)

            @connection
            async def my_method(self, session=None):
                return "fine"

        await MyDAO().my_method()

        mock_session.rollback.assert_not_called()