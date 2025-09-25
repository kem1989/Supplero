"""
Tool registry: central catalog of callable tools, their input/output schemas,
capabilities, and RBAC scopes. Lightweight and framework-agnostic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, Optional


ToolCallable = Callable[[Dict[str, Any], Any, Any], Awaitable[Dict[str, Any]]]


@dataclass
class ToolSpec:
    name: str
    description: str
    handler: ToolCallable
    category: str = "general"
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    required_scopes: list[str] = field(default_factory=list)
    timeout_seconds: int = 30


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        key = spec.name.lower()
        if key in self._tools:
            raise ValueError(f"Tool already registered: {spec.name}")
        self._tools[key] = spec

    def get(self, name: str) -> Optional[ToolSpec]:
        return self._tools.get(name.lower())

    def list_tools(self) -> Dict[str, ToolSpec]:
        return dict(self._tools)


# Singleton-like default registry for simple usage
default_tool_registry = ToolRegistry()



