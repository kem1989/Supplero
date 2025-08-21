"""
Shared semantic contract search service to perform high-precision RAG over
contract contents and return normalized semantic matches with supplier linking
metadata when available.
"""

import os
import json
from dataclasses import dataclass
from typing import List, Optional

import structlog
from sqlalchemy.orm import Session

logger = structlog.get_logger(__name__)


@dataclass
class SemanticMatch:
    document_id: str
    supplier_id: Optional[str]
    supplier_name: Optional[str]
    relevance_score: float
    key_excerpts: List[str]
    match_reasons: List[str]
    document_filename: Optional[str] = None
    extracted_values: Optional[dict] = None


class SemanticContractSearchService:
    """Shared service for semantic contract search across handlers."""

    def __init__(self):
        self.min_relevance_threshold = 0.7
        self.max_excerpts_per_match = 3

    async def search_contracts_semantically(
        self,
        query_text: str,
        db: Session,
        organization_id: int,
        max_results: int = 50,
    ) -> List[SemanticMatch]:
        """
        Execute a precise, conservative semantic search across processed documents.
        Uses the existing direct RAG semantic search logic from contract handlers.
        """
        try:
            # Local import to avoid circulars
            from app.api.v1.handlers.contract_handlers import _direct_rag_semantic_search
            from app.models.document import Document

            # We need a lightweight user surrogate with organization_id for reuse
            class _OrgUser:
                def __init__(self, organization_id: int):
                    self.organization_id = organization_id

            # Run the existing RAG function to obtain normalized docs with scores/excerpts
            rag_results = await _direct_rag_semantic_search(
                query=query_text,
                db=db,
                current_user=_OrgUser(organization_id),
            )

            if not rag_results:
                return []

            # Build lookup to enrich with metadata from DB
            doc_ids = [r.get("id") for r in rag_results if r.get("id") is not None]
            documents = (
                db.query(Document)
                .filter(Document.id.in_(doc_ids))
                .all()
            )
            id_to_doc = {str(d.id): d for d in documents}

            semantic_matches: List[SemanticMatch] = []
            for r in rag_results[:max_results]:
                try:
                    relevance = float(r.get("relevance_score", 0.0))
                except Exception:
                    relevance = 0.0
                if relevance < self.min_relevance_threshold:
                    continue

                doc_id = str(r.get("id"))
                db_doc = id_to_doc.get(doc_id)
                extracted_metadata = (db_doc.extracted_metadata if db_doc else {}) or {}

                # Derive supplier name robustly
                supplier_id = None
                supplier_name = None
                if isinstance(extracted_metadata, dict):
                    supplier_id = extracted_metadata.get("supplier_id")
                    supplier_name = extracted_metadata.get("supplier_name")
                    # Try parties array
                    if not supplier_name:
                        parties = extracted_metadata.get("parties") or []
                        for party in parties:
                            try:
                                if (party.get("value") or "").lower() == "supplier":
                                    context = party.get("context") or ""
                                    # Heuristic: next line or inline after 'SUPPLIER:'
                                    if "SUPPLIER:" in context:
                                        lines = context.splitlines()
                                        for i, line in enumerate(lines):
                                            if "SUPPLIER:" in line and i + 1 < len(lines):
                                                supplier_name = lines[i + 1].strip()
                                                break
                                    if not supplier_name and context:
                                        supplier_name = context.strip().split("\n")[0][:120]
                                    if supplier_name:
                                        break
                            except Exception:
                                continue
                # Fallback to AI extracted supplier_name in RAG result
                if not supplier_name:
                    supplier_name = r.get("supplier_name")

                match = SemanticMatch(
                    document_id=doc_id,
                    supplier_id=supplier_id,
                    supplier_name=supplier_name,
                    relevance_score=relevance,
                    key_excerpts=(r.get("key_excerpts") or [])[: self.max_excerpts_per_match],
                    match_reasons=r.get("match_reasons") or [],
                    document_filename=(db_doc.filename if db_doc else r.get("filename")),
                    extracted_values=self._extract_numeric_values(
                        text=(db_doc.extracted_text if db_doc and db_doc.extracted_text else ""),
                        query_text=query_text,
                    ),
                )
                semantic_matches.append(match)

            return semantic_matches

        except Exception as e:
            logger.error("Semantic contract search failed", error=str(e), exc_info=True)
            return []

    def _extract_numeric_values(self, text: str, query_text: str) -> dict:
        """Lightweight numeric value extraction aligned with target queries."""
        import re

        values = {}
        q = query_text.lower()

        if any(t in q for t in ["days", "termination", "notice"]):
            day_matches = re.findall(r"(\d+)\s*days?", text, re.IGNORECASE)
            if day_matches:
                values["days_found"] = [int(d) for d in day_matches]

        if any(t in q for t in ["liability", "cap", "$", "amount"]):
            currency_matches = re.findall(r"\$([0-9,]+(?:\.[0-9]+)?)\s*([MmKkBb])?", text)
            if currency_matches:
                amounts = []
                for amt_str, unit in currency_matches:
                    base = float(amt_str.replace(",", ""))
                    if unit:
                        u = unit.lower()
                        if u == "m":
                            base *= 1_000_000
                        elif u == "k":
                            base *= 1_000
                        elif u == "b":
                            base *= 1_000_000_000
                    amounts.append(base)
                if amounts:
                    values["amounts_found"] = amounts

        if any(t in q for t in ["payment", "net"]):
            net_matches = re.findall(r"net\s*(\d+)", text, re.IGNORECASE)
            if net_matches:
                values["net_terms_days_found"] = [int(d) for d in net_matches]

        return values


