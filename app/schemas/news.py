from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NewsItemBase(BaseModel):
    title: str
    body_markdown: str
    source_url: str | None = None
    is_published: bool = False


class NewsItemCreate(NewsItemBase):
    pass


class NewsItemUpdate(BaseModel):
    title: str | None = None
    body_markdown: str | None = None
    source_url: str | None = None
    is_published: bool | None = None


class NewsItemOut(NewsItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    published_at: datetime | None
    created_at: datetime
