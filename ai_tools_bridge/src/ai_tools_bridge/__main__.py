"""Entry point: ``python -m ai_tools_bridge``"""

import uvicorn

uvicorn.run(
    "ai_tools_bridge.server:app",
    host="0.0.0.0",
    port=8000,
    log_level="info",
)
