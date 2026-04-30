from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.news import NewsItem
from app.schemas.news import NewsItemCreate, NewsItemUpdate


async def list_news(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    published_only: bool = True,
) -> list[NewsItem]:
    query = select(NewsItem)
    if published_only:
        query = query.where(NewsItem.is_published == True)  # noqa: E712
    query = query.order_by(NewsItem.published_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    return result.scalars().all()  # type: ignore[return-value]


async def create_news(db: AsyncSession, data: NewsItemCreate) -> NewsItem:
    item = NewsItem(
        **data.model_dump(),
        published_at=datetime.now(timezone.utc) if data.is_published else None,
    )
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return item


async def update_news(db: AsyncSession, item: NewsItem, data: NewsItemUpdate) -> NewsItem:
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(item, field, value)
    if data.is_published and not item.published_at:
        item.published_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(item)
    return item


async def delete_news(db: AsyncSession, item: NewsItem) -> None:
    await db.delete(item)
    await db.flush()
