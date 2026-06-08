"""Tests for pagination types and SqlAlchemyRepositoryBase.find_paginated."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.types.pagination import PageParams, PageResult
from app.infra.db.base import Base
from app.infra.db.repositories.base_repository import SqlAlchemyRepositoryBase


class _PaginationTestModel(Base):
    __tablename__ = "pagination_test_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)


class _PaginationTestRepository(SqlAlchemyRepositoryBase):
    def __init__(self, session: Session):
        super().__init__(session, _PaginationTestModel)


@pytest.fixture
def pagination_repo():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine, tables=[_PaginationTestModel.__table__])
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    repo = _PaginationTestRepository(session)

    base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
    for i in range(5):
        repo.create(
            name=f"item-{i}",
            created_at=base_time + timedelta(hours=i),
        )

    yield repo
    session.close()
    engine.dispose()


class TestPageParams:
    def test_from_page_first_page(self):
        params = PageParams.from_page(page=1, page_size=10)
        assert params.offset == 0
        assert params.limit == 10

    def test_from_page_second_page(self):
        params = PageParams.from_page(page=2, page_size=10)
        assert params.offset == 10
        assert params.limit == 10

    def test_from_page_custom_page_size(self):
        params = PageParams.from_page(page=3, page_size=5)
        assert params.offset == 10
        assert params.limit == 5

    def test_rejects_invalid_offset(self):
        with pytest.raises(ValueError, match="offset must be >= 0"):
            PageParams(offset=-1, limit=10)

    def test_rejects_invalid_limit(self):
        with pytest.raises(ValueError, match="limit must be >= 1"):
            PageParams(offset=0, limit=0)

    def test_from_page_rejects_invalid_page(self):
        with pytest.raises(ValueError, match="page must be >= 1"):
            PageParams.from_page(page=0, page_size=10)

    def test_from_page_rejects_invalid_page_size(self):
        with pytest.raises(ValueError, match="page_size must be >= 1"):
            PageParams.from_page(page=1, page_size=0)


class TestPageResult:
    def test_page_result_holds_items_and_total(self):
        result = PageResult(items=["a", "b"], total=10)
        assert result.items == ["a", "b"]
        assert result.total == 10


class TestFindPaginated:
    def test_returns_total_count(self, pagination_repo):
        items, total = pagination_repo.find_paginated()
        assert total == 5
        assert len(items) == 5

    def test_respects_limit(self, pagination_repo):
        items, total = pagination_repo.find_paginated(limit=2)
        assert total == 5
        assert len(items) == 2

    def test_respects_offset(self, pagination_repo):
        items, total = pagination_repo.find_paginated(offset=2, limit=2)
        assert total == 5
        assert len(items) == 2
        assert [item.name for item in items] == ["item-2", "item-1"]

    def test_default_order_by_created_at_desc(self, pagination_repo):
        items, _ = pagination_repo.find_paginated(limit=5)
        assert [item.name for item in items] == [
            "item-4",
            "item-3",
            "item-2",
            "item-1",
            "item-0",
        ]

    def test_order_by_created_at_asc(self, pagination_repo):
        items, _ = pagination_repo.find_paginated(
            limit=5, sort_type="asc"
        )
        assert [item.name for item in items] == [
            "item-0",
            "item-1",
            "item-2",
            "item-3",
            "item-4",
        ]

    def test_filter_by_kwargs(self, pagination_repo):
        pagination_repo.create(
            name="special",
            created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        )
        items, total = pagination_repo.find_paginated(name="special")
        assert total == 1
        assert len(items) == 1
        assert items[0].name == "special"

    def test_empty_result(self, pagination_repo):
        items, total = pagination_repo.find_paginated(name="nonexistent")
        assert total == 0
        assert items == []

    def test_offset_beyond_total_returns_empty(self, pagination_repo):
        items, total = pagination_repo.find_paginated(offset=100, limit=10)
        assert total == 5
        assert items == []
