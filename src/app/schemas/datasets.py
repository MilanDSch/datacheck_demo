from datetime import datetime

from pydantic import BaseModel, ConfigDict

from ..db.models import Visibility


class DatasetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    rows: int
    visibility: Visibility
    created_at: datetime


class DatasetVisibilityUpdate(BaseModel):
    visibility: Visibility
