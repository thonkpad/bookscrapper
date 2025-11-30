from datetime import datetime

from pydantic import BaseModel


class BookDetails(BaseModel):
    title: str
    cover: str
    category: str
    ratings: int
    description: str
    information: Dict[str, Any]
    retrieved_at: datetime = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
