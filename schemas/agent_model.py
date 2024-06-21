from datetime import datetime

from pydantic import BaseModel, field_validator

from schemas.accelerometer_model import AccelerometerData
from schemas.gps_model import GpsData


class AgentData(BaseModel):
    accelerometer: AccelerometerData
    gps: GpsData
    timestamp: datetime

    @classmethod
    @field_validator('timestamp', mode='before')
    def check_timestamp(cls, value):
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(value)
        except (TypeError, ValueError):
            raise ValueError(
                "Invalid timestamp format. Expected ISO 8601 format(YYYY-MM-DDTHH:MM:SSZ)."
            )
