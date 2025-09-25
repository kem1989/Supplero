"""
Context assembler: builds enriched execution context from request, user, org, and
optional page state. Keeps inputs explicit and auditable.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


def build_execution_context(
    *,
    raw_query: str,
    current_user: Any,
    organization_id: Optional[int],
    page_context: Optional[Dict[str, Any]] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    context: Dict[str, Any] = {
        "raw_query": raw_query,
        "user": {
            "id": getattr(current_user, "id", None),
            "email": getattr(current_user, "email", None),
        },
        "organization": {"id": organization_id},
    }

    if page_context:
        context["page_context"] = dict(page_context)

    if extra:
        context["extra"] = dict(extra)

    return context



