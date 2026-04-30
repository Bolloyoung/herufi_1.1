from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas.contact import ContactSubmissionCreate, SubscribeRequest
from app.schemas.insight import InsightPostOut
from app.schemas.news import NewsItemOut
from app.schemas.prediction import PredictionOut, TrackRecordStats
from app.services import contact as contact_svc
from app.services import insights as insights_svc
from app.services import predictions as predictions_svc
from app.services.news import list_news

router = APIRouter(prefix="/api", tags=["public"])


@router.get("/insights", response_model=list[InsightPostOut])
async def get_insights(
    domain: str | None = Query(None),
    tag: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> list[InsightPostOut]:
    posts, _ = await insights_svc.list_insights(db, domain=domain, tag=tag, page=page, page_size=page_size)
    return [InsightPostOut.model_validate(p) for p in posts]


@router.get("/insights/{slug}", response_model=InsightPostOut)
async def get_insight(slug: str, db: AsyncSession = Depends(get_db)) -> InsightPostOut:
    post = await insights_svc.get_insight_by_slug(db, slug)
    if not post or not post.is_published:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insight not found")
    return InsightPostOut.model_validate(post)


@router.get("/news", response_model=list[NewsItemOut])
async def get_news(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> list[NewsItemOut]:
    items = await list_news(db, page=page, page_size=page_size)
    return [NewsItemOut.model_validate(i) for i in items]


@router.get("/predictions", response_model=list[PredictionOut])
async def get_predictions(
    domain: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> list[PredictionOut]:
    preds = await predictions_svc.list_predictions(db, domain=domain, page=page, page_size=page_size)
    return [PredictionOut.model_validate(p) for p in preds]


@router.get("/track-record/stats", response_model=TrackRecordStats)
async def get_track_record(db: AsyncSession = Depends(get_db)) -> TrackRecordStats:
    return await predictions_svc.get_track_record_stats(db)


@router.post("/contact", status_code=status.HTTP_201_CREATED)
async def submit_contact(data: ContactSubmissionCreate, db: AsyncSession = Depends(get_db)) -> dict:
    await contact_svc.create_submission(db, data)
    return {"detail": "Message received. We'll be in touch."}


@router.post("/subscribe", status_code=status.HTTP_201_CREATED)
async def subscribe(data: SubscribeRequest, db: AsyncSession = Depends(get_db)) -> dict:
    await contact_svc.subscribe(db, data.email)
    return {"detail": "Subscribed successfully."}
