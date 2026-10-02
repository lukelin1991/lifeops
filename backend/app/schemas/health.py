import datetime

from pydantic import BaseModel


class WeightCreate(BaseModel):
    weight: float
    measurement_date: datetime.date

class WeightUpdate(BaseModel):
    weight: float | None = None
    measurement_date: datetime.date | None = None

class WeightGoalCreate(BaseModel):
    starting_weight: float
    goal_weight: float

class WeightGoalUpdate(BaseModel):
    starting_weight: float | None = None
    goal_weight: float | None = None
