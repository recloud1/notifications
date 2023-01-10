import uvicorn

from core.config import envs

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        reload=True,
        host=envs.app.host,
        port=envs.app.port,
        log_level="info",
    )
