import json
from typing import List
from typing import Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, Response
from fastapi.exceptions import HTTPException
from sqlalchemy import (
    MetaData,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Table,
    create_engine,
    insert
)
from sqlalchemy.orm import sessionmaker, Session

from config import DATABASE_URL
from schemas.processed_agent_in_db_model import ProcessedAgentDataInDB
from schemas.processed_agent_model import ProcessedAgentData

engine = create_engine(DATABASE_URL)
metadata = MetaData()

# Define the ProcessedAgentData table
processed_agent_data = Table(
    "processed_agent_data",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("road_state", String),
    Column("x", Float),
    Column("y", Float),
    Column("z", Float),
    Column("latitude", Float),
    Column("longitude", Float),
    Column("timestamp", DateTime),
)

metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)


def get_db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# FastAPI app setup
app = FastAPI(swagger_ui_parameters={"syntaxHighlight.theme": "obsidian"})
# WebSocket subscriptions
subscriptions: Set[WebSocket] = set()


@app.get("/")
def home():
    return {"ping": "pong"}


@app.post("/processed_agent_data/")
def create_processed_agent_data(data: List[ProcessedAgentData], db: Session = Depends(get_db)):
    flat_data = [{
        "road_state": d.road_state,
        "x": d.agent_data.accelerometer.x,
        "y": d.agent_data.accelerometer.y,
        "z": d.agent_data.accelerometer.z,
        "latitude": d.agent_data.gps.latitude,
        "longitude": d.agent_data.gps.longitude,
        "timestamp": d.agent_data.timestamp
    } for d in data]

    query = insert(processed_agent_data).values(flat_data)
    db.execute(query)
    db.commit()
    send_data_to_subscribers(data)
    return Response(status_code=200)


@app.get("/processed_agent_data/{processed_agent_data_id}", response_model=ProcessedAgentDataInDB)
def read_processed_agent_data(processed_agent_data_id: int, db: Session = Depends(get_db)):
    instance = db.query(processed_agent_data).filter(processed_agent_data.c.id == processed_agent_data_id).first()
    if instance is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return instance


@app.get("/processed_agent_data/", response_model=list[ProcessedAgentDataInDB])
def list_processed_agent_data(db: Session = Depends(get_db)):
    instances = db.query(processed_agent_data).all()
    return instances


@app.put("/processed_agent_data/{processed_agent_data_id}", response_model=ProcessedAgentDataInDB)
def update_processed_agent_data(processed_agent_data_id: int, data: ProcessedAgentData, db: Session = Depends(get_db)):
    instance_query = db.query(processed_agent_data).filter(processed_agent_data.c.id == processed_agent_data_id)
    instance = instance_query.first()
    if instance is None:
        raise HTTPException(status_code=404, detail="Item not found")
    instance_query.update(
        {
            "road_state": data.road_state,
            "x": data.agent_data.accelerometer.x,
            "y": data.agent_data.accelerometer.y,
            "z": data.agent_data.accelerometer.z,
            "latitude": data.agent_data.gps.latitude,
            "longitude": data.agent_data.gps.longitude,
            "timestamp": data.agent_data.timestamp,
        }
    )

    db.commit()
    return db.query(processed_agent_data).filter(processed_agent_data.c.id == processed_agent_data_id).first()


@app.delete("/processed_agent_data/{processed_agent_data_id}", response_model=ProcessedAgentDataInDB)
def delete_processed_agent_data(processed_agent_data_id: int, db: Session = Depends(get_db)):
    instance_query = db.query(processed_agent_data).filter(processed_agent_data.c.id == processed_agent_data_id)
    instance = instance_query.first()
    if instance is None:
        raise HTTPException(status_code=404, detail="Item not found")

    instance_query.delete()
    db.commit()
    return instance


@app.websocket("/ws/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    subscriptions.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        subscriptions.remove(websocket)


# Function to send data to subscribed users
async def send_data_to_subscribers(data):
    for websocket in subscriptions:
        await websocket.send_json(json.dumps(data))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
