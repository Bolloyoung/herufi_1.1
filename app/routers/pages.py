import markdown
import bleach
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.services import insights as insights_svc
from app.services import predictions as predictions_svc
from app.services.news import list_news

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="app/templates")

ALLOWED_TAGS = list(bleach.sanitizer.ALLOWED_TAGS) + [
    "p", "h1", "h2", "h3", "h4", "h5", "h6", "pre", "code",
    "blockquote", "table", "thead", "tbody", "tr", "th", "td",
    "ul", "ol", "li", "img", "hr", "br", "strong", "em",
]

def _render_md(text: str) -> str:
    html = markdown.markdown(text, extensions=["tables", "fenced_code", "toc"])
    return bleach.clean(html, tags=ALLOWED_TAGS, strip=True)

def _base_ctx(request: Request) -> dict:
    return {"request": request, "now": datetime.now(timezone.utc)}


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: AsyncSession = Depends(get_db)) -> HTMLResponse:
    featured, _ = await insights_svc.list_insights(db, page=1, page_size=3)
    stats = await predictions_svc.get_track_record_stats(db)
    return templates.TemplateResponse("pages/home.html", {
        **_base_ctx(request),
        "featured_posts": featured,
        "stats": stats,
    })


@router.get("/profile", response_class=HTMLResponse)
async def profile(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("pages/profile.html", _base_ctx(request))


@router.get("/insights", response_class=HTMLResponse)
async def insights_page(
    request: Request,
    domain: str | None = Query(None),
    tag: str | None = Query(None),
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    page_size = 9
    posts, total = await insights_svc.list_insights(
        db, domain=domain, tag=tag, page=page, page_size=page_size
    )
    return templates.TemplateResponse("pages/insights.html", {
        **_base_ctx(request),
        "posts": posts,
        "domain": domain,
        "tag": tag,
        "page": page,
        "has_next": total > page * page_size,
    })


@router.get("/insights/{slug}", response_class=HTMLResponse)
async def insight_detail(
    slug: str, request: Request, db: AsyncSession = Depends(get_db)
) -> HTMLResponse:
    post = await insights_svc.get_insight_by_slug(db, slug)
    if not post or not post.is_published:
        return HTMLResponse("<h1>404 — Not Found</h1>", status_code=404)
    return templates.TemplateResponse("pages/insight_detail.html", {
        **_base_ctx(request),
        "post": post,
        "body_html": _render_md(post.body_markdown),
    })


@router.get("/news", response_class=HTMLResponse)
async def news_page(
    request: Request,
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    page_size = 10
    items = await list_news(db, page=page, page_size=page_size + 1)
    has_next = len(items) > page_size
    rendered = [
        {**item.__dict__, "body_html": _render_md(item.body_markdown)}
        for item in items[:page_size]
    ]
    return templates.TemplateResponse("pages/news.html", {
        **_base_ctx(request),
        "items": rendered,
        "page": page,
        "has_next": has_next,
    })


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(
    request: Request,
    domain: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    predictions = await predictions_svc.list_predictions(db, domain=domain, page_size=40)
    return templates.TemplateResponse("pages/dashboard.html", {
        **_base_ctx(request),
        "predictions": predictions,
        "domain": domain,
    })


@router.get("/track-record", response_class=HTMLResponse)
async def track_record_page(
    request: Request, db: AsyncSession = Depends(get_db)
) -> HTMLResponse:
    stats = await predictions_svc.get_track_record_stats(db)
    # Build simple equity curve from resolved predictions in order
    from sqlalchemy import select
    from app.models.prediction import Prediction
    result = await db.execute(
        select(Prediction)
        .where(Prediction.is_correct != None)  # noqa: E711
        .order_by(Prediction.predicted_at)
    )
    resolved = result.scalars().all()
    labels, data, correct = [], [], 0
    for i, p in enumerate(resolved, 1):
        if p.is_correct:
            correct += 1
        labels.append(p.predicted_at.strftime("%b %d"))
        data.append(round(correct / i, 4))

    return templates.TemplateResponse("pages/track_record.html", {
        **_base_ctx(request),
        "stats": stats,
        "equity_labels": labels,
        "equity_data": data,
    })


@router.get("/contact", response_class=HTMLResponse)
async def contact_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("pages/contact.html", _base_ctx(request))


@router.get("/admin", response_class=HTMLResponse)
async def admin_login_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("pages/admin_login.html", _base_ctx(request))


@router.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard_page(request: Request) -> HTMLResponse:
    # Auth is handled client-side via localStorage JWT; server just serves the shell.
    return templates.TemplateResponse("pages/admin_dashboard.html", _base_ctx(request))
