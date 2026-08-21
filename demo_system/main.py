"""Application entry point."""

import uvicorn

from demo_system.app import create_app

app = create_app()


def run() -> None:
    uvicorn.run("demo_system.main:app", host="0.0.0.0", port=8000, reload=False)
