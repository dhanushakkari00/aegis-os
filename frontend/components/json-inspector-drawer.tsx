"use client";

import { Braces } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
  DialogTrigger
} from "@/components/ui/dialog";

export function JSONInspectorDrawer({ payload }: { payload: unknown }) {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="secondary">
          <Braces className="h-4 w-4" />
          Machine JSON
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogTitle className="font-display text-2xl text-white">Machine-readable JSON</DialogTitle>
        <DialogDescription className="mt-2 text-sm text-slate-300">
          Export-friendly structured output for downstream systems.
        </DialogDescription>
        <pre className="mt-6 flex-1 overflow-auto rounded-[24px] border border-white/10 bg-white/5 p-5 text-xs leading-6 text-slate-100">
          {JSON.stringify(payload, null, 2)}
        </pre>
      </DialogContent>
    </Dialog>
  );
}

