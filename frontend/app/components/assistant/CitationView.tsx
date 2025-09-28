"use client";

import React from "react";

type Citation = {
  document_id?: number | string;
  page?: number;
  clause_type?: string;
  text?: string;
  confidence?: number;
};

export default function CitationView({ citations }: { citations: Citation[] }) {
  if (!Array.isArray(citations) || citations.length === 0) return null;
  return (
    <div className="space-y-2">
      {citations.map((c, i) => (
        <div key={i} className="text-xs border rounded p-2">
          <div className="font-medium">{c.clause_type || "Clause"} · Doc {c.document_id} · Pg {c.page}</div>
          {c.text && <div className="text-gray-700 mt-1 line-clamp-3">{c.text}</div>}
          {c.confidence != null && <div className="text-gray-500 mt-1">Confidence: {Math.round((c.confidence || 0) * 100) / 100}</div>}
        </div>
      ))}
    </div>
  );
}











