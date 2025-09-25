"use client";

import React from "react";
import Link from "next/link";

type AssistantPanelProps = {
  isOpen: boolean;
  onClose: () => void;
  pageContext?: Record<string, unknown>;
};

type ExecuteResponse = {
  tool_name: string;
  result: Record<string, any>;
  execution_time_ms: number;
  performance_met: boolean;
  error_message?: string | null;
};

export default function AssistantPanel({ isOpen, onClose, pageContext }: AssistantPanelProps) {
  const [query, setQuery] = React.useState("");
  const [isLoading, setIsLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [data, setData] = React.useState<ExecuteResponse | null>(null);
  const [tools, setTools] = React.useState<Array<{ name: string; description: string }>>([]);

  React.useEffect(() => {
    async function fetchTools() {
      try {
        const res = await fetch("/api/v1/ai-assistant/tools", { method: "GET" });
        if (!res.ok) return;
        const json = await res.json();
        setTools((json?.tools || []).map((t: any) => ({ name: t.name, description: t.description })));
      } catch {
        // ignore tools fetch errors for now
      }
    }
    if (isOpen) fetchTools();
  }, [isOpen]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setData(null);
    try {
      const res = await fetch("/api/v1/ai-assistant/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, context: pageContext || {} }),
      });
      if (!res.ok) {
        const txt = await res.text();
        throw new Error(txt || "Request failed");
      }
      const json: ExecuteResponse = await res.json();
      setData(json);
    } catch (err: any) {
      setError(err?.message || "Something went wrong");
    } finally {
      setIsLoading(false);
    }
  }

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[9998] flex items-end md:items-center md:justify-end">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative w-full md:w-[640px] h-[82vh] md:h-[92vh] glass rounded-t-2xl md:rounded-2xl overflow-hidden flex flex-col border">
        <div className="flex items-center justify-between px-4 py-3 border-b bg-slate-800/70">
          <div className="font-semibold text-slate-100">AI Assistant</div>
          <button onClick={onClose} className="text-sm text-slate-300 hover:text-slate-50 focus-ring">Close</button>
        </div>

        <div className="p-4 overflow-y-auto flex-1 space-y-4">
          <form onSubmit={handleSubmit} className="space-y-3">
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask anything across suppliers and contracts..."
              className="w-full bg-slate-900/50 border rounded-md p-3 min-h-[96px] text-slate-100 placeholder:text-slate-400 focus-ring"
            />
            <div className="flex items-center gap-2">
              <button
                type="submit"
                disabled={isLoading || !query.trim()}
                className="px-4 py-2 rounded-md disabled:opacity-50 text-slate-900 bg-blue-500 hover:bg-blue-400 focus-ring"
              >
                {isLoading ? "Thinking…" : "Ask"}
              </button>
              {tools.length > 0 && (
                <div className="text-xs text-slate-400">{tools.length} tools available</div>
              )}
            </div>
          </form>

          {error && (
            <div className="text-sm text-red-400">{error}</div>
          )}

          {data && (
            <div className="space-y-3">
              <div className="text-sm text-slate-400">Tool: {data.tool_name} · {Math.round(data.execution_time_ms)} ms</div>
              {data.error_message && (
                <div className="text-sm text-red-400">{data.error_message}</div>
              )}
              <ResponseView result={data.result} onClose={onClose} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ResponseView({ result, onClose }: { result: Record<string, any>; onClose: () => void }) {
  // Handle multi-part query responses
  if (result?.is_multi_part) {
    return <MultiPartResponseView result={result} onClose={onClose} />;
  }

  // Handle single intent responses
  const message = result?.message || (typeof result?.summary === "string" ? result.summary : null);
  const items = Array.isArray(result?.items) ? result.items : null;
  const citations = result?.citations || result?.evidence?.citations || [];
  const risk = result?.risk_factors || result?.evidence?.risk_factors || [];
  const contracts = Array.isArray(result?.contracts) ? result.contracts : [];
  const suppliers = Array.isArray(result?.suppliers) ? result.suppliers : [];

  return (
    <div className="space-y-4">
      {message && <div className="text-base text-slate-100">{message}</div>}
      {items && items.length > 0 && (
        <ul className="list-disc pl-6 text-sm text-slate-200">
          {items.map((it: any, idx: number) => (
            <li key={idx}>{typeof it === "string" ? it : JSON.stringify(it)}</li>
          ))}
        </ul>
      )}
             <LinkedResults contracts={contracts} suppliers={suppliers} onClose={onClose} />
      <div className="grid md:grid-cols-2 gap-4">
        <div>
          <h4 className="font-medium text-sm mb-1 text-slate-200">Citations</h4>
          <CitationList citations={citations} onClose={onClose} />
        </div>
        <div>
          <h4 className="font-medium text-sm mb-1 text-slate-200">Risk Factors</h4>
          <RiskList factors={risk} />
        </div>
      </div>
      {!message && !items && (
        <pre className="text-xs bg-slate-900/50 border p-3 rounded-md overflow-x-auto text-slate-200">{JSON.stringify(result, null, 2)}</pre>
      )}
    </div>
  );
}

function MultiPartResponseView({ result, onClose }: { result: Record<string, any>; onClose: () => void }) {
  const results = result?.results || {};
  const retrieval = results?.retrieval || {};
  const explanations = results?.explanations || {};
  const insights = results?.insights || {};

  return (
    <div className="space-y-6">
      {/* Intent Classification */}
      {result?.intent_classification && (
        <div className="text-sm text-slate-400">
          Intent: {result.intent_classification.primary_intent} 
          (Confidence: {Math.round((result.intent_classification.overall_confidence || 0) * 100)}%)
        </div>
      )}

      {/* Search Results */}
      {retrieval?.has_results && (
        <div>
          <h4 className="font-medium text-lg mb-3 text-slate-200 flex items-center gap-2">
            {retrieval.title || "🔍 Search Results"}
            <span className="text-sm text-slate-400">({retrieval.count || 0})</span>
          </h4>
          <div className="space-y-2">
            {Array.isArray(retrieval.data) && retrieval.data.map((item: any, idx: number) => (
              <div key={idx} className="border rounded-lg p-3 bg-slate-900/40">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium text-slate-200">{item.name}</div>
                    <div className="text-sm text-slate-400">{item.description}</div>
                    {item.type && (
                      <span className="inline-block mt-1 px-2 py-1 text-xs rounded-full bg-slate-700 text-slate-300">
                        {item.type}
                      </span>
                    )}
                  </div>
                         {item.link && (
                           <Link 
                             href={item.link} 
                             className="text-blue-400 hover:text-blue-300 underline underline-offset-2"
                             onClick={onClose}
                           >
                             View
                           </Link>
                         )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Explanations */}
      {explanations?.has_results && (
        <div>
          <h4 className="font-medium text-lg mb-3 text-slate-200">
            {explanations.title || "💡 Explanations"}
          </h4>
          <div className="space-y-3">
            {Array.isArray(explanations.data) && explanations.data.map((item: any, idx: number) => (
              <div key={idx} className="border rounded-lg p-4 bg-slate-900/40">
                <div className="font-medium text-slate-200 mb-2">{item.title}</div>
                <div className="text-sm text-slate-300 whitespace-pre-wrap">{item.content}</div>
                {item.confidence && (
                  <div className="text-xs text-slate-400 mt-2">
                    Confidence: {Math.round((item.confidence || 0) * 100)}%
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Insights */}
      {insights?.has_results && (
        <div>
          <h4 className="font-medium text-lg mb-3 text-slate-200">
            {insights.title || "📊 Insights"}
          </h4>
          <div className="space-y-3">
            {Array.isArray(insights.data) && insights.data.map((item: any, idx: number) => (
              <div key={idx} className="border rounded-lg p-4 bg-slate-900/40">
                <div className="font-medium text-slate-200 mb-2">{item.title}</div>
                <div className="text-sm text-slate-300 whitespace-pre-wrap">{item.content}</div>
                {item.confidence && (
                  <div className="text-xs text-slate-400 mt-2">
                    Confidence: {Math.round((item.confidence || 0) * 100)}%
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Summary */}
      {result?.summary && (
        <div className="text-sm text-slate-400 border-t pt-3">
          Components: {result.summary.total_components || 0} • 
          Retrieval: {result.summary.retrieval_success ? "✅" : "❌"} • 
          Explanations: {result.summary.explanation_success ? "✅" : "❌"} • 
          Insights: {result.summary.insights_success ? "✅" : "❌"}
        </div>
      )}
    </div>
  );
}

function CitationList({ citations, onClose }: { citations: any[]; onClose: () => void }) {
  if (!Array.isArray(citations) || citations.length === 0) return <div className="text-xs text-slate-400">None</div>;
  return (
    <ul className="space-y-2">
      {citations.map((c, i) => (
        <li key={i} className="text-xs border rounded p-2 bg-slate-900/40">
          <div className="font-medium text-slate-200">{c.clause_type || "Clause"} · Doc {c.document_id} · Pg {c.page}</div>
          {c.text && <div className="text-slate-300 mt-1 line-clamp-3">{c.text}</div>}
          {c.confidence != null && <div className="text-slate-400 mt-1">Confidence: {Math.round((c.confidence || 0) * 100) / 100}</div>}
          <div className="mt-2">
            <DeepLink label="View in Documents" href={buildDocumentHref(c?.document_id, c?.page)} onClose={onClose} />
          </div>
        </li>
      ))}
    </ul>
  );
}

function RiskList({ factors }: { factors: any[] }) {
  if (!Array.isArray(factors) || factors.length === 0) return <div className="text-xs text-slate-400">None</div>;
  return (
    <ul className="space-y-2">
      {factors.map((f, i) => (
        <li key={i} className="text-xs border rounded p-2 bg-slate-900/40">
          <div className="font-medium text-slate-200">{f.name || "Factor"}</div>
          {f.value != null && <div className="text-slate-300">Value: {String(f.value)}</div>}
          {f.weight != null && <div className="text-slate-300">Weight: {String(f.weight)}</div>}
          {f.impact != null && <div className="text-slate-300">Impact: {String(f.impact)}</div>}
          {f.evidence && <div className="text-slate-300 mt-1 line-clamp-3">{String(f.evidence)}</div>}
        </li>
      ))}
    </ul>
  );
}

function LinkedResults({ contracts, suppliers, onClose }: { contracts: any[]; suppliers: any[]; onClose: () => void }) {
  if ((!contracts || contracts.length === 0) && (!suppliers || suppliers.length === 0)) return null;
  return (
    <div className="space-y-3">
      {contracts && contracts.length > 0 && (
        <div>
          <h4 className="font-medium text-sm mb-1 text-slate-2 00">Contracts</h4>
          <ul className="space-y-2">
            {contracts.map((c: any, idx: number) => {
              const id = c?.id || c?.document_id || c?.documentId;
              const name = c?.title || c?.name || `Contract ${id}`;
              const href = c?.href || buildDocumentHref(id);
              return (
                <li key={idx} className="text-sm">
                  <DeepLink label={name} href={href} onClose={onClose} />
                </li>
              );
            })}
          </ul>
        </div>
      )}
      {suppliers && suppliers.length > 0 && (
        <div>
          <h4 className="font-medium text-sm mb-1 text-slate-200">Suppliers</h4>
          <ul className="space-y-2">
            {suppliers.map((s: any, idx: number) => {
              const id = s?.id || s?.supplier_id;
              const name = s?.name || `Supplier ${id}`;
              const href = s?.href || buildSupplierHref(id);
              return (
                <li key={idx} className="text-sm">
                  <DeepLink label={name} href={href} onClose={onClose} />
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}

function DeepLink({ label, href, onClose }: { label: string; href?: string; onClose?: () => void }) {
  if (!href) return <span className="text-slate-400">{label}</span>;
  return (
    <Link 
      href={href} 
      className="text-blue-400 hover:text-blue-300 underline underline-offset-2"
      onClick={onClose}
    >
      {label}
    </Link>
  );
}

function buildDocumentHref(id?: string | number, page?: number) {
  if (!id) return undefined;
  const params = new URLSearchParams();
  params.set("documentId", String(id));
  if (page != null) params.set("page", String(page));
  return `/documents?${params.toString()}`;
}

function buildSupplierHref(id?: string | number) {
  if (!id) return undefined;
  const params = new URLSearchParams();
  params.set("ids", String(id));
  return `/suppliers?${params.toString()}`;
}


