"""
Deterministic tool runner with simple parallelization, timeouts, and error capture.
Not a full agent; intentionally minimal.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Tuple

import structlog

from .registry import ToolSpec


logger = structlog.get_logger(__name__)


class ToolRunner:
    def __init__(self) -> None:
        pass

    async def run_tool(self, spec: ToolSpec, parameters: Dict[str, Any], db: Any, current_user: Any) -> Dict[str, Any]:
        try:
            with asyncio.timeout(spec.timeout_seconds):
                return await spec.handler(parameters, db, current_user)
        except TimeoutError:
            logger.warning("Tool execution timed out", tool=spec.name)
            return {"success": False, "error": f"Tool '{spec.name}' timed out"}
        except Exception as exc:  # noqa: BLE001
            logger.error("Tool execution failed", tool=spec.name, error=str(exc), exc_info=True)
            return {"success": False, "error": str(exc)}

    async def run_tools_in_parallel(self, jobs: List[Tuple[ToolSpec, Dict[str, Any]]], db: Any, current_user: Any) -> List[Dict[str, Any]]:
        tasks = [self.run_tool(spec, params, db, current_user) for spec, params in jobs]
        return await asyncio.gather(*tasks, return_exceptions=False)



