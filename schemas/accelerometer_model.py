from pydantic import BaseModel


class AccelerometerData(BaseModel):
    x: float
    y: float
    z: float
