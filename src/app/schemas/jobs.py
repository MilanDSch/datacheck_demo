from pydantic import BaseModel, ConfigDict, Field


class JobCreate(BaseModel):
    dataset_id: int = Field(gt=0)


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dataset_id: int
    status: str
    error: str | None = None


class ReportOut(BaseModel):
    job_id: int
    quality_score: int
