## Cross-System Natural Language Queries for Supplier Discovery

### What’s already implemented
- **AI Assistant routing**: Natural language → intent classification → parameter extraction → handler execution in `backend/app/api/v1/ai_assistant.py` with comprehensive intents in `ai_assistant_utils/intent_classifier.py` and parameter extraction in `ai_assistant_utils/parameter_extractor.py`.
- **Cross-system handlers**: Supplier–contract bridge handlers in `backend/app/api/v1/handlers/cross_system_handlers.py`.
- **Cross-system search service**: Supplier–contract orchestration in `backend/app/core/cross_system_search.py` (risky contracts, expiring contracts, clauses, value, unified risk).
- **RAG/semantic document search**: Robust semantic contract search in `backend/app/api/v1/handlers/contract_handlers.py` via `_direct_rag_semantic_search` and `_rag_semantic_search_fallback` (Elasticsearch-first, RAG fallback).
- **Supplier linking**: Automatic linking of `Document` → supplier via extracted metadata in `backend/app/core/supplier_linking.py` (sets `extracted_metadata.supplier_name` and `supplier_id`).
- **Frontend NLQ UI**: Supplier Discovery uses unified endpoint `/ai-assistant/execute` and already transforms responses in `frontend/app/components/SupplierDiscovery.tsx`.

### Gaps to support the target queries
- **Query classification granularity**: Needs consistent mapping for clause-specific and thresholded queries (e.g., termination > 30 days, liability cap < $1M, payment terms > Net 30, data security).
- **Structured clause data**: Ensure clause types and numeric attributes (days, amounts) are extracted and queryable, or provide a semantic fallback when structured data is missing.
- **Cross-system RAG orchestration**: Bridge semantic document matches back to suppliers and unify results when Elasticsearch/structured data is insufficient.
- **Unified UX**: Surface both supplier-level results and contract-level insights (excerpts, match reasons) in Supplier Discovery.

### Recommended steps
1) Intent and parameter extraction enhancements
   - Add/confirm clause type mappings and synonyms in `intent_classifier.py` and `parameter_extractor.py`:
     - force_majeure → ["force majeure", "act of god", "beyond reasonable control"]
     - termination → extract `termination_notice_days` or `termination_days_min`
     - liability_cap → extract `liability_cap_max_amount`
     - payment_terms → extract `payment_terms_days_min`
     - data_security → ["data security", "information security", "security requirements"]
   - Extend parameter extraction prompt to parse numeric thresholds and units:
     - “longer than 30 days” → `termination_days_min = 31`
     - “under $1M” → `liability_cap_max_amount = 1000000`
     - “longer than Net 30” → `payment_terms_days_min = 31`
   - Add unit tests for extraction of numbers, currencies, and days.

2) Semantic clause detection service (shared RAG)
   - Refactor `_direct_rag_semantic_search` from `contract_handlers.py` into a shared service (e.g., `backend/app/core/semantic_contract_search.py`) exposing:
     - `search_contracts_semantically(query_text, db, organization_id) -> List[SemanticMatch]` with `document_id, relevance_score, supplier_name, key_excerpts, match_reasons, extracted_values`.
   - Keep existing strict precision rules (reject weak matches; enforce relevance ≥ 0.7; include excerpts and reasons).

3) Cross-system orchestration via semantic matches
   - Add new query type in `backend/app/core/cross_system_search.py`:
     - `SUPPLIERS_BY_SEMANTIC_CONTRACTS`
   - Implement `_search_suppliers_by_semantic_contracts(request, db, org_id)`:
     - Call shared semantic search with `request.query_text`.
     - Group matches by supplier (prefer `extracted_metadata.supplier_id`, fall back to exact/fuzzy supplier name match).
     - Build `SupplierContractInfo` aggregates (contract_count, total_contract_value if derivable) and collect top matching `ContractSupplierInfo` with excerpts.
   - Return unified `CrossSystemSearchResponse` with both supplier and contract results and insights (e.g., top clauses matched, thresholds met).

4) Structured clause querying path (optional but recommended)
   - Ensure `ContractClause` (or `Document.extracted_metadata`) captures:
     - `clause_type` in {force_majeure, termination, liability_cap, payment_terms, data_security}
     - Numeric attributes: `termination_notice_days`, `liability_cap_amount`, `payment_terms_days`
     - Confidence scores and excerpts.
   - Update `_search_suppliers_by_contract_clauses` to accept optional numeric filters:
     - `termination_days_min`, `liability_cap_max_amount`, `payment_terms_days_min`
   - Extend clause extraction pipeline to populate these fields where feasible.

5) Handler wiring and intent mapping
   - Add handler `execute_suppliers_by_semantic_contracts` in `cross_system_handlers.py` that builds a `CrossSystemSearchRequest` with `query_type = SUPPLIERS_BY_SEMANTIC_CONTRACTS` and `query_text = parameters.get("query")`.
   - Add intent `SUPPLIERS_BY_SEMANTIC_CONTRACTS` in `intent_classifier.py` tools description and map it in `ai_assistant.py` → `handlers`.
   - Classification rule of thumb: if query references clause concepts or thresholds and supplier context without explicit structured filters, route to semantic path; otherwise use structured/ES path and only fall back to semantic when needed.

6) Unified response shaping
   - Ensure cross-system responses consistently return:
     - `search_results.suppliers: Supplier[]` and `search_results.contracts: Contract[]`
     - For contracts: `key_excerpts`, `match_reasons`, `relevance_score`
     - `statistics`, `key_insights`, `recommended_actions`
   - If needed, update `ResponseFormatter` to preserve both suppliers and contracts for cross-system results.

7) Frontend UX additions (`SupplierDiscovery.tsx`)
   - When `search_results.contracts` is present, show a collapsible “Matching Contracts” section per supplier with:
     - Contract filename, relevance score, and highlighted `key_excerpts`.
     - Clause badges (e.g., Force Majeure, Termination > 30d, Liability Cap < $1M).
   - Add example queries covering all target scenarios.
   - Display intent and confidence from `query_processing` when available.

8) Tests and validation
   - Backend E2E tests hitting `/ai-assistant/execute` for queries:
     - “Show me suppliers who have contracts with force majeure clauses”
     - “Which vendors have termination clauses longer than 30 days?”
     - “Find suppliers with liability caps under $1M”
     - “Show me all suppliers with payment terms longer than Net 30”
     - “Which contracts mention data security requirements?”
   - Unit tests for parameter extraction (numbers/currencies/days) and cross-system aggregation.
   - Frontend integration test to render supplier cards and matching contract excerpts.

9) Performance and operations
   - Keep ES-first strategy for structured clause and metadata queries; use semantic service when ES/DB produce zero or low-confidence results.
   - Limit semantic analysis to N most recent processed documents; expose org-wide caps and timeouts.
   - Consider ES mappings for clause fields to speed up structured path; revisit vector DB only if scale requires.

### Mapping examples → engine behavior
- “suppliers with force majeure” → `SUPPLIERS_BY_CONTRACT_CLAUSES` with `clause_types=["force_majeure"]` → ES/DB path; fallback to semantic if needed.
- “termination clauses longer than 30 days” → `SUPPLIERS_BY_CONTRACT_CLAUSES` with `termination_days_min=31`; if absent in DB, use `SUPPLIERS_BY_SEMANTIC_CONTRACTS` with query_text.
- “liability caps under $1M” → `SUPPLIERS_BY_CONTRACT_CLAUSES` with `liability_cap_max_amount=1000000`; semantic fallback.
- “payment terms longer than Net 30” → `payment_terms_days_min=31`; semantic fallback.
- “contracts mention data security requirements” → primarily semantic path, then bridge back to suppliers.

### Rollout order (safe increments)
1. Param extraction upgrades + tests.
2. Shared semantic service + new cross-system query type + handler wiring.
3. Frontend contract insights rendering.
4. Structured clause numeric filters (if extraction available) + ES mappings.
5. E2E tests and performance guards.


