from typing import List
from pydantic import BaseModel, Field


class AgentActionRequest(BaseModel):
    agent_id: str
    action: str
    risk_score: float = Field(ge=0.0, le=1.0)
    requested_tools: List[str] = []


class GovernanceDecision(BaseModel):
    decision: str
    reason: str
    requires_human_review: bool