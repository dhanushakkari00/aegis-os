"use client";

import { Accessibility, Waves } from "lucide-react";

import { Switch } from "@/components/ui/switch";
import { useAccessibility } from "@/hooks/use-accessibility";

export function AccessibilityToggle() {
  const { state, setHighContrast, setReducedMotion } = useAccessibility();

  return (
    <div className="flex flex-wrap items-center justify-end gap-4 rounded-full border border-white/10 bg-white/5 px-4 py-2">
      <div className="flex items-center gap-2 text-xs text-slate-300">
        <Accessibility className="h-4 w-4 text-cyan" />
        <span>High contrast</span>
        <Switch
          aria-label="Toggle high contrast mode"
          checked={state.highContrast}
          onCheckedChange={setHighContrast}
        />
      </div>
      <div className="flex items-center gap-2 text-xs text-slate-300">
        <Waves className="h-4 w-4 text-surge" />
        <span>Reduce motion</span>
        <Switch
          aria-label="Toggle reduced motion mode"
          checked={state.reducedMotion}
          onCheckedChange={setReducedMotion}
        />
      </div>
    </div>
  );
}

