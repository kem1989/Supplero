"use client";

import React from "react";

type CommandBarProps = {
  onOpenAssistant: () => void;
};

export default function CommandBar({ onOpenAssistant }: CommandBarProps) {
  React.useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const isMac = /Mac|iPod|iPhone|iPad/.test(navigator.platform);
      if ((isMac && e.metaKey && e.key.toLowerCase() === "k") || (!isMac && e.ctrlKey && e.key.toLowerCase() === "k")) {
        e.preventDefault();
        onOpenAssistant();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onOpenAssistant]);

  return (
    <button
      onClick={onOpenAssistant}
      className="fixed bottom-4 right-4 z-[9999] px-4 py-2 rounded-md shadow gradient-primary text-slate-900"
      aria-label="Open AI Assistant (⌘K)"
      title="Open AI Assistant (⌘K)"
    >
      Assistant
    </button>
  );
}


