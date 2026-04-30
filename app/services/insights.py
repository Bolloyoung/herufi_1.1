from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.insight import InsightPost
from app.schemas.insight import InsightPostCreate, InsightPostUpdate


async def list_insights(
    db: AsyncSession,
    domain: str | None = None,
    tag: str | None = None,
    page: int = 1,
    page_size: int = 10,
    published_only: bool = True,
) -> tuple[list[InsightPost], int]:
    query = select(InsightPost)
    if published_only:
        query = query.where(InsightPost.is_published == True)  # noqa: E712
    if domain:
        query = query.where(InsightPost.domain == domain)
    if tag:
        query = query.where(InsightPost.tags.contains([tag]))

    count_result = await db.execute(query)
    total = len(count_result.scalars().all())

    query = query.order_by(InsightPost.published_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    return result.scalars().all(), total  # type: ignore[return-value]


async def get_insight_by_slug(db: AsyncSession, slug: str) -> InsightPost | None:
    result = await db.execute(select(InsightPost).where(InsightPost.slug == slug))
    return result.scalar_one_or_none()


async def create_insight(
    db: AsyncSession, data: InsightPostCreate, author_id: int
) -> InsightPost:
    post = InsightPost(
        **data.model_dump(),
        author_id=author_id,
        published_at=datetime.now(timezone.utc) if data.is_published else None,
    )
    db.add(post)
    await db.flush()
    await db.refresh(post)
    return post


async def update_insight(
    db: AsyncSession, post: InsightPost, data: InsightPostUpdate
) -> InsightPost:
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(post, field, value)
    if data.is_published and not post.published_at:
        post.published_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(post)
    return post


async def delete_insight(db: AsyncSession, post: InsightPost) -> None:
    await db.delete(post)
    await db.flush()
