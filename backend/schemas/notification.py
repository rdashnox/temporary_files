from pydantic import BaseModel, Field


class NotificationCreate(BaseModel):
    user_id: int | None = None
    title: str = Field(..., min_length=3, max_length=160)
    message: str = Field(..., min_length=3, max_length=1000)
    channel: str = Field(default="in_app", max_length=40)
    entity_type: str | None = Field(default=None, max_length=80)
    entity_id: str | None = Field(default=None, max_length=80)


class NotificationUpdate(BaseModel):
    is_read: bool = True
