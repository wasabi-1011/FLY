"""通用 schema：分页、消息。"""
from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Msg(BaseModel):
    detail: str


class PageOut(BaseModel, Generic[T]):
    total: int
    page: int
    page_size: int
    items: list[T]


def paginate(total: int, page: int, page_size: int, items: list[T]) -> PageOut[T]:
    return PageOut(total=total, page=page, page_size=page_size, items=items)
