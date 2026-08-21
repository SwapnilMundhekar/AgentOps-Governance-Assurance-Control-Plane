from typing import Literal

from fastapi import FastAPI, HTTPException, Query

from app.audit import get_audit_records, log_governance_decision
from app.models import AgentActionRequest, GovernanceDecision

app = FastAPI(
    title="AgentOps Governance & Assurance Control Plane",
    description=(
        "Governance, assurance, policy evaluation, "
        "and audit control plane for AI agents."
    ),
    version="0.5.0",
)


@app.get("/")
def root():
    return {
        "service": "AgentOps Governance & Assurance Control Plane",
        "version": "0.5.0",
        "status": "running",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "agentops-governance-control-plane",
    }


@app.post("/validate-manifest")
def validate_manifest(manifest: dict):
    required_fields = [
        "agent_id",
        "name",
        "version",
        "owner",
        "purpose",
    ]

    missing_fields = [
        field
        for field in required_fields
        if field not in manifest
    ]

    if missing_fields:
        raise HTTPException(
            status_code=400,
            detail={
                "valid": False,
                "missing_fields": missing_fields,
            },
        )

    return {
        "valid": True,
        "message": "Agent manifest is valid.",
        "manifest": manifest,
    }


@app.post("/register-agent")
def register_agent(manifest: dict):
    required_fields = [
        "agent_id",
        "name",
        "version",
        "owner",
        "purpose",
    ]

    missing_fields = [
        field
        for field in required_fields
        if field not in manifest
    ]

    if missing_fields:
        raise HTTPException(
            status_code=400,
            detail={
                "registered": False,
                "missing_fields": missing_fields,
            },
        )

    return {
        "registered": True,
        "agent_id": manifest["agent_id"],
        "message": "Agent registered successfully.",
    }


@app.post(
    "/governance/evaluate",
    response_model=GovernanceDecision,
)
def evaluate_governance(
    request: AgentActionRequest,
):
    if request.risk_score >= 0.8:
        decision = "BLOCK"
        reason = "Risk score exceeds the blocking threshold."

    elif request.risk_score >= 0.5:
        decision = "REVIEW"
        reason = "Risk score requires human review."

    else:
        decision = "ALLOW"
        reason = "Risk score is within the allowed threshold."

    result = GovernanceDecision(
        decision=decision,
        reason=reason,
        risk_score=request.risk_score,
    )

    log_governance_decision(
        agent_id=request.agent_id,
        action=request.action,
        risk_score=request.risk_score,
        decision=decision,
        reason=reason,
    )

    return result


@app.get("/audit")
def get_audit(
    limit: int = Query(
        default=50,
        ge=1,
        le=500,
        description="Maximum number of audit records to return.",
    ),
    agent_id: str | None = Query(
        default=None,
        description="Filter audit records by agent ID.",
    ),
    decision: Literal["ALLOW", "REVIEW", "BLOCK"] | None = Query(
        default=None,
        description="Filter audit records by governance decision.",
    ),
):
    records = get_audit_records(
        limit=limit,
        agent_id=agent_id,
        decision=decision,
    )

    return {
        "count": len(records),
        "filters": {
            "agent_id": agent_id,
            "decision": decision,
            "limit": limit,
        },
        "records": records,
    }