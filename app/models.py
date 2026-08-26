from typing import Literal

from pydantic import BaseModel, Field


class AgentActionRequest(BaseModel):
    agent_id: str

    action: str

    risk_score: float = Field(
        ge=0.0,
        le=1.0,
    )


class GovernanceDecision(BaseModel):
    decision: Literal[
        "ALLOW",
        "REVIEW",
        "BLOCK",
    ]

    reason: str

    risk_score: float

    policy_id: int

    policy_name: str

    policy_version: int


class PolicyCreate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=100,
    )

    review_threshold: float = Field(
        ge=0.0,
        le=1.0,
    )

    block_threshold: float = Field(
        ge=0.0,
        le=1.0,
    )