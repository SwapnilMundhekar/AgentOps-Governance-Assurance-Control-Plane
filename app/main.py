from typing import Literal

from fastapi import FastAPI, HTTPException, Query

from app.agents import (
    get_agents,
    get_agent_versions,
    register_agent_record,
)

from app.audit import (
    get_audit_records,
    log_governance_decision,
)

from app.models import (
    AgentActionRequest,
    AgentRegisterRequest,
    GovernanceDecision,
    PolicyApprovalRequest,
    PolicyCreate,
    PolicyVersionCreate,
)

from app.policies import (
    activate_policy,
    approve_policy,
    create_policy,
    create_policy_version,
    get_active_policy,
    get_policies,
    get_policy_versions,
)


app = FastAPI(
    title="AgentOps Governance & Assurance Control Plane",
    description=(
        "Governance, assurance, policy evaluation, "
        "agent registry, and audit control plane "
        "for AI agents."
    ),
    version="1.0.0",
)


@app.get("/")
def root():
    return {
        "service": (
            "AgentOps Governance & Assurance Control Plane"
        ),
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "agentops-governance-control-plane",
    }


@app.post("/validate-manifest")
def validate_manifest(
    manifest: dict,
):
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


@app.post(
    "/register-agent",
    status_code=201,
)
def register_agent(
    agent: AgentRegisterRequest,
):
    try:
        registered_agent = register_agent_record(
            agent_id=agent.agent_id,
            name=agent.name,
            version=agent.version,
            owner=agent.owner,
            purpose=agent.purpose,
            risk_tier=agent.risk_tier,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    return {
        "registered": True,
        "message": "Agent registered successfully.",
        "agent": registered_agent,
    }


@app.get("/agents")
def list_agents(
    limit: int = Query(
        default=50,
        ge=1,
        le=500,
    ),
    status: Literal[
        "REGISTERED",
        "SUSPENDED",
        "RETIRED",
    ] | None = Query(
        default=None,
    ),
    risk_tier: Literal[
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
    ] | None = Query(
        default=None,
    ),
):
    agents = get_agents(
        limit=limit,
        status=status,
        risk_tier=risk_tier,
    )

    return {
        "count": len(agents),
        "filters": {
            "status": status,
            "risk_tier": risk_tier,
            "limit": limit,
        },
        "agents": agents,
    }


@app.get("/agents/{agent_id}")
def get_registered_agent(
    agent_id: str,
):
    versions = get_agent_versions(
        agent_id
    )

    if not versions:
        raise HTTPException(
            status_code=404,
            detail="Agent not found.",
        )

    return {
        "agent_id": agent_id,
        "count": len(versions),
        "versions": versions,
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

    review_threshold = (
        policy["review_threshold"]
    )

    block_threshold = (
        policy["block_threshold"]
    )

    if (
        request.risk_score
        >= block_threshold
    ):
        decision = "BLOCK"

        reason = (
            f"Risk score exceeds block threshold "
            f"{block_threshold}."
        )

    elif (
        request.risk_score
        >= review_threshold
    ):
        decision = "REVIEW"

        reason = (
            f"Risk score exceeds review threshold "
            f"{review_threshold}."
        )

    else:
        decision = "ALLOW"

        reason = (
            "Risk score is below the "
            "review threshold."
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
            review_threshold=(
                policy.review_threshold
            ),
            block_threshold=(
                policy.block_threshold
            ),
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    return {
        "message": (
            "Governance policy created as DRAFT."
        ),
        "policy": created_policy,
    }


@app.get(
    "/policies/{policy_id}/versions"
)
def list_policy_versions(
    policy_id: int,
):
    versions = get_policy_versions(
        policy_id
    )

    if versions is None:
        raise HTTPException(
            status_code=404,
            detail="Governance policy not found.",
        )

    return {
        "count": len(versions),
        "versions": versions,
    }


@app.post(
    "/policies/{policy_id}/versions"
)
def add_policy_version(
    policy_id: int,
    policy: PolicyVersionCreate,
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
        new_version = create_policy_version(
            policy_id=policy_id,
            review_threshold=(
                policy.review_threshold
            ),
            block_threshold=(
                policy.block_threshold
            ),
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    if new_version is None:
        raise HTTPException(
            status_code=404,
            detail="Governance policy not found.",
        )

    return {
        "message": (
            "New policy version created as DRAFT."
        ),
        "policy": new_version,
    }


@app.post(
    "/policies/{policy_id}/approve"
)
def approve_governance_policy(
    policy_id: int,
    request: PolicyApprovalRequest,
):
    try:
        policy = approve_policy(
            policy_id=policy_id,
            approved_by=request.approved_by,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    if policy is None:
        raise HTTPException(
            status_code=404,
            detail="Governance policy not found.",
        )

    return {
        "message": "Governance policy approved.",
        "policy": policy,
    }


@app.post(
    "/policies/{policy_id}/activate"
)
def set_active_policy(
    policy_id: int,
):
    try:
        policy = activate_policy(
            policy_id
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    if policy is None:
        raise HTTPException(
            status_code=404,
            detail="Governance policy not found.",
        )

    return {
        "message": "Governance policy activated.",
        "policy": policy,
    }