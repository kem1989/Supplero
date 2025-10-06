## Future Update: NL-Driven Supplier Risk and Contract Analysis Blueprint

### Target data model (normalized, analytics-ready)
- **Supplier core**
  - suppliers: core profile, org_id, lifecycle flags
  - supplier_profiles: time-versioned attributes (size, industry, geography)
- **Contracts and documents**
  - contracts: contract-level entity (type, status, effective_at, expires_at, auto_renewal, governing_law, jurisdiction)
  - contract_parties: internal party, counterparty, roles
  - contract_terms: normalized key terms (payment, termination, liability caps, SLAs)
  - contract_clauses: clause instances with canonical type, text spans, risk flags
  - contract_documents: link to `documents` (source artifact, versions)
- **Risk and signals**
  - risk_assessments: time-series per supplier (and optionally per contract), category scores (financial, ESG, operational, compliance), overall_score, source, inputs_snapshot, reasoning
  - risk_signals: discrete events (sanction hit, adverse news, delivery delay), severity, confidence, source, linked_entities
  - watchlist_entries: who added, why, status
- **External data**
  - news_articles: deduped articles, enriched with sentiment/relevance/keywords, entity matches, provenance
  - financial_metrics: standardized indicators (rev, margins, liquidity, leverage, trends) per period
  - sanctions_hits: provider, list, matched_entity, adjudication, status
  - esg_ratings: provider, dimensioned scores, methodology/version
- **Operations/monitoring**
  - alerts: rule_id, subscriber, channel, trigger, last_fired_at, status
  - alert_rules: query/rule definition (e.g., sanction_added=true), throttle windows, severity
  - jobs: ingestion jobs, schedules, last_run, run_state, retry/backoff metadata
- **Indexes and search**
  - text indexes on names, parties, clauses
  - composite indexes for time-window and status queries (expires_at, auto_renewal, risk_level)

### Ingestion & enrichment architecture
- **Schedulers & orchestration**
  - Cron/scheduled jobs for news, sanctions, financials, ESG; on-demand backfills; idempotent runs
- **Connectors**
  - News API: pull recent, dedupe (hash URL/title+published_at), sentiment + risk keyword tagging, supplier/entity resolution
  - Sanctions/PEP: nightly full and hourly delta; fuzzy matching + human-in-the-loop adjudication queue
  - Financials: quarterly pulls (public) or ERP integration (private); standardize to common schema with units/currency
  - ESG: provider API with methodology versioning; store raw + normalized
- **Contract pipeline**
  - Upload → OCR (if needed) → text extraction → metadata extraction → clause classification → linkage to supplier(s)
  - Provenance log: model/version, prompts, confidence, chunks used
  - QA gates: quality scores, human validation tasks for low-confidence extractions
- **Matching & linking**
  - Supplier resolution: rules + org scoping; store match_confidence and alternative candidates
  - Contract-to-supplier linkage: deterministic (IDs, emails, legal names) fallback to fuzzy/semantic; human override path
- **Idempotency, retries, and backpressure**
  - Source-side cursors or since_timestamps; job_run_id; exactly-once upserts by natural keys
  - Exponential backoff, circuit breakers, and per-provider rate limits
- **Data governance**
  - Source metadata and versions stored on every record; PII tagging; retention policies; consent/compliance flags

### Risk scoring and analytics
- **Scoring services**
  - Category-specific scorers (financial, ESG, operational, compliance) producing normalized 0–100 with explanations
  - Aggregator: weighted blend with per-category weights; store inputs_snapshot and justification
- **Benchmarks & rules**
  - Industry and region benchmarks (payment terms, DPO, standard clauses)
  - Rule engine for red flags (e.g., unlimited liability, non-favorable jurisdiction)
- **Trends**
  - Rolling windows (30/90/365 days) for score deltas, volatility, signal counts

### Natural Language Interface (tools/handlers)
- **Intent coverage extensions**
  - Risk monitoring: “alert me if…”, “show recent news…”
  - Contract lifecycle: “renewals in next 90 days”, “auto-renewal clauses”, “unfavorable payment terms vs industry”
  - Combined: “high-risk suppliers with expiring contracts”, “contracts tied to suppliers failing ESG”
- **Parameter extraction**
  - Supplier names, time windows, categories (financial/ESG/ops), thresholds, jurisdictions, benchmarks, comparison sets
- **Execution routing**
  - Handlers call prebuilt query functions over normalized schema and text search where needed
- **Confidence & grounding**
  - Low-confidence clarifications; cite sources (contract IDs, clause excerpts, news links); show reasoning and inputs
- **RAG/semantic**
  - Use text search and fuzzy matching to answer clause-level and profile-level queries with citations

### Monitoring, alerts, and subscriptions
- **Alerting model**
  - Users subscribe at supplier/segment level; rule templates (sanction addition, score drop > X, adverse news > threshold, delivery delays > threshold)
- **Delivery**
  - In-app notifications, email, webhook/Slack; throttling and digest modes
- **Auditability**
  - Persist alert firings, evaluations, and user acknowledgements

### Observability, audit, and quality
- **Full audit trail**
  - Store NL queries, classified intent, parameters, tool executions, results metadata; access-scoped
- **Data quality dashboards**
  - Coverage (suppliers with contracts, with financials, with ESG), extraction confidence distributions, matching error rates
- **Evaluation harness**
  - Golden datasets for clause extraction and intent classification; regression checks on model/version changes

### Privacy, security, and tenancy
- **Tenant isolation**
  - Strong org scoping in all queries and indexes; encryption at rest for sensitive fields
- **Secrets & compliance**
  - Secret management for provider keys; logging scrubbing; deletion workflows; retention per data class

### Phased rollout (pragmatic milestones)
- **Phase 1**: Schema extension for contracts/clauses, risk_assessments, news_articles; embed pipelines for clauses; extend NLI for renewals/clauses queries
- **Phase 2**: Sanctions + financials ingestion; category scorers; monitoring rules and alert delivery
- **Phase 3**: ESG integration; benchmarking; combined cross-functional NL handlers; dashboards and report generation
- **Phase 4**: Human review flows, evaluation harness, and quality dashboards; fine-tune thresholds and weights


