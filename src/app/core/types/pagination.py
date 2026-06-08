from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class PageParams:
    """Core/Infra 分頁參數，對齊 SQL OFFSET / LIMIT。"""

    offset: int = 0
    limit: int = 10

    def __post_init__(self) -> None:
        if self.offset < 0:
            raise ValueError("offset must be >= 0")
        if self.limit < 1:
            raise ValueError("limit must be >= 1")

    @classmethod
    def from_page(cls, page: int, page_size: int) -> "PageParams":
        """將 API 層的 page / page_size 轉換為 offset / limit。"""
        if page < 1:
            raise ValueError("page must be >= 1")
        if page_size < 1:
            raise ValueError("page_size must be >= 1")
        return cls(offset=(page - 1) * page_size, limit=page_size)


@dataclass
class PageResult(Generic[T]):
    """分頁查詢結果；page 元資料由 API 層組裝 PaginatedData。"""

    items: list[T]
    total: int
