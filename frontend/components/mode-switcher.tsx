import type { CaseMode } from "@/lib/types";
import { cn } from "@/lib/utils";

const options: { value: CaseMode; label: string; description: string }[] = [
  {
    value: "auto_detect",
    label: "Auto Detect",
    description: "Let the system classify the case type."
  },
  {
    value: "medical_triage",
    label: "Medical Triage",
    description: "Prioritize symptoms, red flags, and handoff safety."
  },
  {
    value: "disaster_response",
    label: "Disaster Response",
    description: "Focus on hazards, entrapment, and field coordination."
  }
];

export function ModeSwitcher({
  value,
  onChange
}: {
  value: CaseMode;
  onChange: (value: CaseMode) => void;
}) {
  return (
    <div className="grid gap-3 md:grid-cols-3" role="tablist" aria-label="Case mode">
      {options.map((option) => {
        const active = option.value === value;
        return (
          <button
            key={option.value}
            type="button"
            role="tab"
            aria-selected={active}
            onClick={() => onChange(option.value)}
            className={cn(
              "rounded-[24px] border p-4 text-left transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan/70",
              active
                ? "border-cyan/30 bg-cyan/10 shadow-glow"
                : "border-white/10 bg-white/5 hover:bg-white/10"
            )}
          >
            <p className="font-display text-base font-semibold text-white">{option.label}</p>
            <p className="mt-2 text-sm leading-6 text-slate-300">{option.description}</p>
          </button>
        );
      })}
    </div>
  );
}

