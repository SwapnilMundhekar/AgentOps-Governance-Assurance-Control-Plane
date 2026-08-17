from contextlib import asynccontextmanager

import yaml
from fastapi import FastAPI
from pydantic import BaseModel

from app.validator import validate_manifest
from app.registry import init_db, register_agent


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="AgentOps Governance & Assurance Control Plane",
    lifespan=lifespan
)


class ManifestRequest(BaseModel):
    manifest_path: str
    schema_path: str


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