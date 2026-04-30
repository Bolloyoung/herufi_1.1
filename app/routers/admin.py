from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.user import User
from app.routers.deps import require_admin
from app.schemas.contact import ContactSubmissionOut
from app.schemas.insight import InsightPostCreate, InsightPostOut, InsightPostUpdate
from app.schemas.news import NewsItemCreate, NewsItemOut, NewsItemUpdate
from app.schemas.prediction import PredictionCreate, PredictionOut, PredictionResolve, PredictionUpdate
from app.services import contact as contact_svc
from app.services import insights as insights_svc
from app.services import predictions as predictions_svc
from app.services.news import create_news, delete_news, list_news, update_news

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ── Insights ──────────────────────────────────────────────────────────────────

@router.get("/insights", response_model=list[InsightPostOut])
async def admin_list_insights(
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[InsightPostOut]:
    posts, _ = await insights_svc.list_insights(db, page=page, published_only=False)
    return [InsightPostOut.model_validate(p) for p in posts]


@router.post("/insights", response_model=InsightPostOut, status_code=status.HTTP_201_CREATED)
async def admin_create_insight(
    data: InsightPostCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> InsightPostOut:
    post = await insights_svc.create_insight(db, data, author_id=admin.id)
    return InsightPostOut.model_validate(post)


@router.patch("/insights/{slug}", response_model=InsightPostOut)
async def admin_update_insight(
    slug: str,
    data: InsightPostUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> InsightPostOut:
    post = await insights_svc.get_insight_by_slug(db, slug)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insight not found")
    post = await insights_svc.update_insight(db, post, data)
    return InsightPostOut.model_validate(post)


@router.delete("/insights/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_insight(
    slug: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> None:
    post = await insights_svc.get_insight_by_slug(db, slug)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insight not found")
    await insights_svc.delete_insight(db, post)


# ── News ──────────────────────────────────────────────────────────────────────

@router.get("/news", response_model=list[NewsItemOut])
async def admin_list_news(
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[NewsItemOut]:
    items = await list_news(db, page=page, published_only=False)
    return [NewsItemOut.model_validate(i) for i in items]


@router.post("/news", response_model=NewsItemOut, status_code=status.HTTP_201_CREATED)
async def admin_create_news(
    data: NewsItemCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> NewsItemOut:
    item = await create_news(db, data)
    return NewsItemOut.model_validate(item)


@router.patch("/news/{item_id}", response_model=NewsItemOut)
async def admin_update_news(
    item_id: int,
    data: NewsItemUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> NewsItemOut:
    from sqlalchemy import select
    result = await db.execute(
        select(__import__("app.models.news", fromlist=["NewsItem"]).NewsItem).where(
            __import__("app.models.news", fromlist=["NewsItem"]).NewsItem.id == item_id
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="News item not found")
    item = await update_news(db, item, data)
    return NewsItemOut.model_validate(item)


@router.delete("/news/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_news(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> None:
    from sqlalchemy import select
    from app.models.news import NewsItem
    result = await db.execute(select(NewsItem).where(NewsItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="News item not found")
    await delete_news(db, item)


# ── Predictions ───────────────────────────────────────────────────────────────

@router.post("/predictions", response_model=PredictionOut, status_code=status.HTTP_201_CREATED)
async def admin_create_prediction(
    data: PredictionCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> PredictionOut:
    pred = await predictions_svc.create_prediction(db, data)
    return PredictionOut.model_validate(pred)


@router.post("/predictions/{pred_id}/resolve", response_model=PredictionOut)
async def admin_resolve_prediction(
    pred_id: int,
    data: PredictionResolve,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> PredictionOut:
    from sqlalchemy import select
    from app.models.prediction import Prediction
    result = await db.execute(select(Prediction).where(Prediction.id == pred_id))
    pred = result.scalar_one_or_none()
    if not pred:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found")
    pred = await predictions_svc.resolve_prediction(db, pred, data)
    return PredictionOut.model_validate(pred)


# ── Contact inbox ─────────────────────────────────────────────────────────────

@router.get("/contact-submissions", response_model=list[ContactSubmissionOut])
async def admin_list_submissions(
    unread_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[ContactSubmissionOut]:
    subs = await contact_svc.list_submissions(db, unread_only=unread_only)
    return [ContactSubmissionOut.model_validate(s) for s in subs]
