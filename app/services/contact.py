from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import ContactSubmission
from app.models.subscriber import Subscriber
from app.schemas.contact import ContactSubmissionCreate


async def create_submission(db: AsyncSession, data: ContactSubmissionCreate) -> ContactSubmission:
    sub = ContactSubmission(**data.model_dump())
    db.add(sub)
    await db.flush()
    await db.refresh(sub)
    return sub


async def list_submissions(db: AsyncSession, unread_only: bool = False) -> list[ContactSubmission]:
    query = select(ContactSubmission).order_by(ContactSubmission.submitted_at.desc())
    if unread_only:
        query = query.where(ContactSubmission.is_read == False)  # noqa: E712
    result = await db.execute(query)
    return result.scalars().all()  # type: ignore[return-value]


async def subscribe(db: AsyncSession, email: str) -> Subscriber:
    result = await db.execute(select(Subscriber).where(Subscriber.email == email))
    existing = result.scalar_one_or_none()
    if existing:
        return existing
    subscriber = Subscriber(email=email)
    db.add(subscriber)
    await db.flush()
    await db.refresh(subscriber)
    return subscriber
