from fastapi import FastAPI

from app.models import AgentActionRequest, GovernanceDecision

app = FastAPI(
    title="AgentOps Governance & Assurance Control Plane",
    version="0.2.0"
)


@app.get("/")
def root():
    return {
        "service": "AgentOps Governance & Assurance Control Plane",
        "status": "running"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/governance/evaluate", response_model=GovernanceDecision)
def evaluate_action(request: AgentActionRequest):

    # High-risk action
    if request.risk_score >= 0.8:
        return GovernanceDecision(
            decision="BLOCK",
            reason="Risk score exceeds governance threshold.",
            requires_human_review=True
        )

    # Medium-risk action
    if request.risk_score >= 0.5:
        return GovernanceDecision(
            decision="REVIEW",
            reason="Action requires human approval.",
            requires_human_review=True
        )

    # Low-risk action
    return GovernanceDecision(
        decision="ALLOW",
        reason="Action is within permitted risk threshold.",
        requires_human_review=False
    )