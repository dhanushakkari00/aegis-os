import type { ReactNode } from "react";

import { CommandHeader } from "@/components/command-header";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-ink text-slate-100">
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute left-[-10%] top-[-15%] h-[420px] w-[420px] rounded-full bg-cyan/10 blur-3xl" />
        <div className="absolute bottom-[-10%] right-[-5%] h-[380px] w-[380px] rounded-full bg-emerald-400/10 blur-3xl" />
        <div className="absolute inset-0 bg-command-grid bg-[size:70px_70px] opacity-[0.08]" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(78,232,255,0.12),transparent_35%),radial-gradient(circle_at_bottom_right,rgba(108,242,180,0.08),transparent_30%),linear-gradient(180deg,#07111b_0%,#050b12_100%)]" />
      </div>
      <div className="relative z-10">
        <CommandHeader />
        <main className="mx-auto flex w-full max-w-7xl flex-col gap-8 px-4 py-8 lg:px-8">
          {children}
        </main>
      </div>
    </div>
  );
}

