from fastapi import FastAPI
from pydantic import BaseModel
from app.validator import validate_manifest

app = FastAPI()


class ManifestRequest(BaseModel):
    manifest_path: str
    schema_path: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/validate-manifest")
def validate_agent_manifest(request: ManifestRequest):
    return validate_manifest(
        request.manifest_path,
        request.schema_path
    )