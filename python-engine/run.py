from __future__ import annotations

import multiprocessing
import os

import uvicorn


if __name__ == "__main__":
    multiprocessing.freeze_support()
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=int(os.getenv("DJ_AGENT_ENGINE_PORT", "17821")),
        log_level=os.getenv("DJ_AGENT_LOG_LEVEL", "info"),
        access_log=False,
    )
