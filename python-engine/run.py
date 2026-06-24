from __future__ import annotations

import multiprocessing
import os
import argparse

import uvicorn

from app.runtime import configure_bundled_ffmpeg

configure_bundled_ffmpeg()

from app.main import app


if __name__ == "__main__":
    multiprocessing.freeze_support()
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=int(os.getenv("DJ_AGENT_ENGINE_PORT", "17821")))
    arguments = parser.parse_args()
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=arguments.port,
        log_level=os.getenv("DJ_AGENT_LOG_LEVEL", "info"),
        access_log=False,
    )
