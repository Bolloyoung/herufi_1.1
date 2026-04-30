from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prediction import Prediction
from app.schemas.prediction import PredictionCreate, PredictionResolve, TrackRecordStats


async def list_predictions(
    db: AsyncSession,
    domain: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> list[Prediction]:
    query = select(Prediction)
    if domain:
        query = query.where(Prediction.domain == domain)
    query = query.order_by(Prediction.predicted_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    return result.scalars().all()  # type: ignore[return-value]


async def create_prediction(db: AsyncSession, data: PredictionCreate) -> Prediction:
    pred = Prediction(**data.model_dump())
    db.add(pred)
    await db.flush()
    await db.refresh(pred)
    return pred


async def resolve_prediction(
    db: AsyncSession, prediction: Prediction, data: PredictionResolve
) -> Prediction:
    prediction.actual_value = data.actual_value
    prediction.is_correct = data.is_correct
    await db.flush()
    await db.refresh(prediction)
    return prediction


async def get_track_record_stats(db: AsyncSession) -> TrackRecordStats:
    result = await db.execute(select(Prediction))
    all_preds = result.scalars().all()

    resolved = [p for p in all_preds if p.is_correct is not None]
    correct = [p for p in resolved if p.is_correct]

    by_domain: dict[str, dict[str, int | float]] = {}
    for p in all_preds:
        d = p.domain
        if d not in by_domain:
            by_domain[d] = {"total": 0, "resolved": 0, "correct": 0, "hit_rate": 0.0}
        by_domain[d]["total"] += 1  # type: ignore[operator]
        if p.is_correct is not None:
            by_domain[d]["resolved"] += 1  # type: ignore[operator]
            if p.is_correct:
                by_domain[d]["correct"] += 1  # type: ignore[operator]

    for domain_stats in by_domain.values():
        res = int(domain_stats["resolved"])
        cor = int(domain_stats["correct"])
        domain_stats["hit_rate"] = round(cor / res, 4) if res else 0.0

    total = len(all_preds)
    res_count = len(resolved)
    cor_count = len(correct)

    return TrackRecordStats(
        total=total,
        resolved=res_count,
        correct=cor_count,
        hit_rate=round(cor_count / res_count, 4) if res_count else 0.0,
        by_domain=by_domain,
    )
