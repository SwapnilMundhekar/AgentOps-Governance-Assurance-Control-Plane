from contextlib import asynccontextmanager

import yaml
from fastapi import FastAPI
from pydantic import BaseModel

from app.models import AgentActionRequest, GovernanceDecision
from app.registry import init_db, register_agent
from app.validator import validate_manifest


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="AgentOps Governance & Assurance Control Plane",
    version="0.2.0",
    lifespan=lifespan
)


class ManifestRequest(BaseModel):
    manifest_path: str
    schema_path: str


@app.get("/")
def root():
    return {
        "service": "AgentOps Governance & Assurance Control Plane",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


@app.post("/validate-manifest")
def validate_agent_manifest(request: ManifestRequest):
    return validate_manifest(
        request.manifest_path,
        request.schema_path
    )


@app.post("/register-agent")
def register_agent_api(request: ManifestRequest):

    validation_result = validate_manifest(
        request.manifest_path,
        request.schema_path
    )

    if not validation_result["valid"]:
        return {
            "registered": False,
            "errors": validation_result["errors"]
        }

    with open(request.manifest_path, "r", encoding="utf-8") as file:
        manifest = yaml.safe_load(file)

    return register_agent(
        name=manifest["name"],
        version=manifest["version"],
        manifest_path=request.manifest_path
    )


@app.post(
    "/governance/evaluate",
    response_model=GovernanceDecision
)
def evaluate_action(request: AgentActionRequest):

    if request.risk_score >= 0.8:
        return GovernanceDecision(
            decision="BLOCK",
            reason="Risk score exceeds governance threshold.",
            requires_human_review=True
        )

    if request.risk_score >= 0.5:
        return GovernanceDecision(
            decision="REVIEW",
            reason="Action requires human approval.",
            requires_human_review=True
        )

    return GovernanceDecision(
        decision="ALLOW",
        reason="Action is within permitted risk threshold.",
        requires_human_review=False
    )