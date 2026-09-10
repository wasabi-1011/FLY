"""后台·CMS 页面管理（FR-B01~B10 / FR-B06 版本回滚 / FR-B03 并发锁）。R2 权限。

版本模型：每次提交区块生成一个 PageVersion（保留 >=10 个），发布即将
page.current_version_id 指向某版本并置 status=published。回滚即改指向。
"""
from __future__ import annotations

import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CurrentContentOps
from app.models.content import Block, Page, PageVersion
from app.schemas.content import (
    BlockBase,
    PageCreate,
    PageOut,
    PageUpdate,
    PageVersionOut,
)
from app.services.audit import log_operation

router = APIRouter(prefix="/api/admin/pages", tags=["admin-cms"])

LOCK_TTL_MIN = 30  # 编辑锁有效期（分钟）


async def _next_version_no(db: AsyncSession, page_id: int) -> int:
    cur = (
        await db.execute(
            select(func.max(PageVersion.version_no)).where(
                PageVersion.page_id == page_id
            )
        )
    ).scalar()
    return (cur or 0) + 1


async def _create_version(
    db: AsyncSession, page_id: int, created_by: int, blocks: list[BlockBase], note: str | None = None
) -> PageVersion:
    version_no = await _next_version_no(db, page_id)
    version = PageVersion(page_id=page_id, version_no=version_no, created_by=created_by, note=note)
    db.add(version)
    await db.flush()
    for b in blocks:
        db.add(
            Block(
                page_version_id=version.id,
                type=b.type,
                config_json=b.config_json,
                sort=b.sort,
                mobile_visible=b.mobile_visible,
            )
        )
    return version


@router.get("", response_model=list[PageOut])
async def list_pages(
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    _: CurrentContentOps = None,
):
    rows = list((await db.execute(select(Page).order_by(Page.id))).scalars().all())
    return [PageOut.model_validate(p).model_dump(mode="json") for p in rows]


@router.post("", response_model=PageOut, status_code=201)
async def create_page(
    payload: PageCreate,
    current: CurrentContentOps,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    if (
        await db.execute(select(Page).where(Page.slug == payload.slug))
    ).scalar_one_or_none():
        raise HTTPException(status_code=409, detail="slug 已存在")
    page = Page(slug=payload.slug, title=payload.title, page_type=payload.page_type, status="draft")
    db.add(page)
    await db.flush()
    await _create_version(db, page.id, current.id, payload.blocks, note="初始版本")
    await db.commit()
    await db.refresh(page)
    await log_operation(db, current, "create", "page", page.id, after=payload.model_dump())
    await db.commit()
    return PageOut.model_validate(page).model_dump(mode="json")


@router.get("/{page_id}", response_model=dict)
async def get_page(
    page_id: int,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    _: CurrentContentOps = None,
):
    page = await db.get(Page, page_id)
    if not page:
        raise HTTPException(status_code=404, detail="页面不存在")
    versions = list(
        (await db.execute(select(PageVersion).where(PageVersion.page_id == page_id)))
        .scalars()
        .all()
    )
    versions_out = [
        PageVersionOut.model_validate(v).model_dump(mode="json") for v in versions
    ]
    return {
        **PageOut.model_validate(page).model_dump(mode="json"),
        "versions": versions_out,
    }


@router.put("/{page_id}", response_model=PageOut)
async def update_page(
    page_id: int,
    payload: PageUpdate,
    current: CurrentContentOps,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    page = await db.get(Page, page_id)
    if not page:
        raise HTTPException(status_code=404, detail="页面不存在")
    # 并发锁检查（FR-B03）
    if (
        page.locked_by
        and page.locked_by != current.id
        and page.locked_at
        and (datetime.datetime.utcnow() - page.locked_at).total_seconds()
        < LOCK_TTL_MIN * 60
    ):
        raise HTTPException(status_code=409, detail="该页面正被其他用户编辑")
    if payload.title is not None:
        page.title = payload.title
    if payload.status is not None:
        page.status = payload.status
    if payload.blocks is not None:
        await _create_version(db, page.id, current.id, payload.blocks, note="编辑提交")
    await db.commit()
    await db.refresh(page)
    await log_operation(db, current, "update", "page", page.id)
    await db.commit()
    return PageOut.model_validate(page).model_dump(mode="json")


@router.post("/{page_id}/lock", status_code=200)
async def acquire_lock(
    page_id: int,
    current: CurrentContentOps,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    page = await db.get(Page, page_id)
    if not page:
        raise HTTPException(status_code=404, detail="页面不存在")
    if (
        page.locked_by
        and page.locked_by != current.id
        and page.locked_at
        and (datetime.datetime.utcnow() - page.locked_at).total_seconds()
        < LOCK_TTL_MIN * 60
    ):
        raise HTTPException(status_code=409, detail="该页面已被其他用户锁定")
    page.locked_by = current.id
    page.locked_at = datetime.datetime.utcnow()
    await db.commit()
    return {"detail": "已锁定", "locked_by": current.id}


@router.post("/{page_id}/unlock", status_code=200)
async def release_lock(
    page_id: int,
    current: CurrentContentOps,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    page = await db.get(Page, page_id)
    if not page:
        raise HTTPException(status_code=404, detail="页面不存在")
    if page.locked_by and page.locked_by != current.id:
        raise HTTPException(status_code=403, detail="仅锁定者可释放")
    page.locked_by = None
    page.locked_at = None
    await db.commit()
    return {"detail": "已释放"}


@router.post("/{page_id}/publish", response_model=PageOut)
async def publish_page(
    page_id: int,
    version_id: int | None = None,
    note: str | None = None,
    current: CurrentContentOps = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """发布（FR-B06/B07）：将某个版本设为当前生效版本。"""
    page = await db.get(Page, page_id)
    if not page:
        raise HTTPException(status_code=404, detail="页面不存在")
    if version_id is None:
        # 取最新版本
        version_id = (
            await db.execute(
                select(func.max(PageVersion.id)).where(
                    PageVersion.page_id == page_id
                )
            )
        ).scalar()
    version = await db.get(PageVersion, version_id)
    if version is None or version.page_id != page_id:
        raise HTTPException(status_code=404, detail="版本不存在")
    page.current_version_id = version.id
    page.status = "published"
    await db.commit()
    await db.refresh(page)
    await log_operation(
        db, current, "publish", "page", page.id,
        after={"version_id": version_id, "note": note},
    )
    await db.commit()
    return PageOut.model_validate(page).model_dump(mode="json")


@router.post("/{page_id}/rollback/{version_id}", response_model=PageOut)
async def rollback_page(
    page_id: int,
    version_id: int,
    current: CurrentContentOps,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """回滚到历史版本（FR-B06）。"""
    page = await db.get(Page, page_id)
    if not page:
        raise HTTPException(status_code=404, detail="页面不存在")
    version = await db.get(PageVersion, version_id)
    if version is None or version.page_id != page_id:
        raise HTTPException(status_code=404, detail="版本不存在")
    page.current_version_id = version.id
    page.status = "published"
    await db.commit()
    await db.refresh(page)
    await log_operation(
        db, current, "rollback", "page", page.id, after={"version_id": version_id}
    )
    await db.commit()
    return PageOut.model_validate(page).model_dump(mode="json")


@router.delete("/{page_id}", status_code=204)
async def delete_page(
    page_id: int,
    current: CurrentContentOps,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    page = await db.get(Page, page_id)
    if not page:
        raise HTTPException(status_code=404, detail="页面不存在")
    if page.status.value != "offline" and page.status.value != "draft":
        raise HTTPException(status_code=400, detail="仅下线/草稿态页面可删除")
    await db.delete(page)
    await db.commit()
    await log_operation(db, current, "delete", "page", page_id)
    await db.commit()
    return None
