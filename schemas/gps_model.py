from pydantic import BaseModel


class GpsData(BaseModel):
    latitude: float
    longitude: float
