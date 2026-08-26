from typing import Literal

from fastapi import FastAPI, HTTPException, Query

from app.audit import (
    get_audit_records,
    log_governance_decision,
)

from app.models import (
    AgentActionRequest,
    GovernanceDecision,
    PolicyCreate,
)

from app.policies import (
    activate_policy,
    create_policy,
    get_active_policy,
    get_policies,
)


app = FastAPI(
    title="AgentOps Governance & Assurance Control Plane",
    description=(
        "Governance, assurance, policy evaluation, "
        "and audit control plane for AI agents."
    ),
    version="0.7.0",
)


@app.get("/")
def root():
    return {
        "service": (
            "AgentOps Governance & Assurance Control Plane"
        ),
        "version": "0.7.0",
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
    policy = get_active_policy()

    if policy is None:
        raise HTTPException(
            status_code=500,
            detail="No active governance policy.",
        )

    review_threshold = policy["review_threshold"]
    block_threshold = policy["block_threshold"]

    if request.risk_score >= block_threshold:
        decision = "BLOCK"

        reason = (
            f"Risk score exceeds block threshold "
            f"{block_threshold}."
        )

    elif request.risk_score >= review_threshold:
        decision = "REVIEW"

        reason = (
            f"Risk score exceeds review threshold "
            f"{review_threshold}."
        )

    else:
        decision = "ALLOW"

        reason = (
            "Risk score is below the review threshold."
        )

    result = GovernanceDecision(
        decision=decision,
        reason=reason,
        risk_score=request.risk_score,
        policy_id=policy["id"],
        policy_name=policy["name"],
        policy_version=policy["version"],
    )

    log_governance_decision(
        agent_id=request.agent_id,
        action=request.action,
        risk_score=request.risk_score,
        decision=decision,
        reason=reason,
        policy_id=policy["id"],
        policy_name=policy["name"],
        policy_version=policy["version"],
    )

    return result


@app.get("/audit")
def get_audit(
    limit: int = Query(
        default=50,
        ge=1,
        le=500,
    ),
    agent_id: str | None = Query(
        default=None,
    ),
    decision: Literal[
        "ALLOW",
        "REVIEW",
        "BLOCK",
    ] | None = Query(
        default=None,
    ),
    policy_id: int | None = Query(
        default=None,
        ge=1,
    ),
):
    records = get_audit_records(
        limit=limit,
        agent_id=agent_id,
        decision=decision,
        policy_id=policy_id,
    )

    return {
        "count": len(records),
        "filters": {
            "agent_id": agent_id,
            "decision": decision,
            "policy_id": policy_id,
            "limit": limit,
        },
        "records": records,
    }


@app.get("/policies")
def list_policies():
    policies = get_policies()

    return {
        "count": len(policies),
        "policies": policies,
    }


@app.post("/policies")
def add_policy(
    policy: PolicyCreate,
):
    if (
        policy.review_threshold
        >= policy.block_threshold
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "review_threshold must be lower "
                "than block_threshold."
            ),
        )

    try:
        created_policy = create_policy(
            name=policy.name,
            review_threshold=policy.review_threshold,
            block_threshold=policy.block_threshold,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    return {
        "message": "Governance policy created.",
        "policy": created_policy,
    }


@app.post("/policies/{policy_id}/activate")
def set_active_policy(
    policy_id: int,
):
    policy = activate_policy(
        policy_id
    )

    if policy is None:
        raise HTTPException(
            status_code=404,
            detail="Governance policy not found.",
        )

    return {
        "message": "Governance policy activated.",
        "policy": policy,
    }