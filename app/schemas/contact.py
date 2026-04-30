from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class ContactSubmissionCreate(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str


class ContactSubmissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    subject: str
    message: str
    submitted_at: datetime
    is_read: bool


class SubscribeRequest(BaseModel):
    email: EmailStr
