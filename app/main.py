from fastapi import FastAPI

app = FastAPI(
    title='AgentOps Governance Control Plane',
    version='0.1.0'
)


@app.get('/')
def root():
    return {
        'service': 'AgentOps Governance Control Plane',
        'version': '0.1.0'
    }


@app.get('/health')
def health_check():
    return {
        'status': 'healthy',
        'service': 'AgentOps Governance Control Plane'
    }
