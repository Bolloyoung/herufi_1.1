from datetime import datetime

from pydantic import BaseModel, ConfigDict


class InsightPostBase(BaseModel):
    title: str
    slug: str
    domain: str
    tags: list[str] = []
    summary: str
    body_markdown: str
    hero_chart_config: dict | None = None
    is_published: bool = False


class InsightPostCreate(InsightPostBase):
    pass


class InsightPostUpdate(BaseModel):
    title: str | None = None
    domain: str | None = None
    tags: list[str] | None = None
    summary: str | None = None
    body_markdown: str | None = None
    hero_chart_config: dict | None = None
    is_published: bool | None = None


class InsightPostOut(InsightPostBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    published_at: datetime | None
    created_at: datetime
    author_id: int | None
