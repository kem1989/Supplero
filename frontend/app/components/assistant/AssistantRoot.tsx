"use client";

import React from "react";
import { useAuth } from "../../contexts/AuthContext";
import AssistantPanel from "./AssistantPanel";
import CommandBar from "./CommandBar";

export default function AssistantRoot() {
  const { user } = useAuth();
  const [open, setOpen] = React.useState(false);
  
  // Only show assistant when user is authenticated
  if (!user) {
    return null;
  }
  
  return (
    <>
      <CommandBar onOpenAssistant={() => setOpen(true)} />
      <AssistantPanel isOpen={open} onClose={() => setOpen(false)} />
    </>
  );
}


