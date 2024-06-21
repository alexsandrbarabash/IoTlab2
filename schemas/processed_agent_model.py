from pydantic import BaseModel

from schemas.agent_model import AgentData


class ProcessedAgentData(BaseModel):
    road_state: str
    agent_data: AgentData
