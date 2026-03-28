"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Shield } from "lucide-react";

import { AccessibilityToggle } from "@/components/accessibility-toggle";
import { cn } from "@/lib/utils";

const links = [
  { href: "/", label: "Intake" },
  { href: "/analyze", label: "Analyze" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/about", label: "About" }
];

export function CommandHeader() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-40 border-b border-white/10 bg-ink/70 backdrop-blur-xl">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-4 px-4 py-4 lg:px-8">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-cyan/20 bg-cyan/10 shadow-glow">
              <Shield className="h-6 w-6 text-cyan" />
            </div>
            <div>
              <h1 className="font-display text-xl font-semibold text-white">Aegis OS</h1>
              <p className="text-sm text-slate-300">
                Emergency intelligence platform
              </p>
            </div>
          </div>
          <AccessibilityToggle />
        </div>
        <nav aria-label="Primary" className="flex flex-wrap items-center gap-2">
          {links.map((link) => {
            const active =
              link.href === "/"
                ? pathname === link.href
                : pathname?.startsWith(link.href);

            return (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "rounded-full border px-4 py-2 text-sm transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan/70",
                  active
                    ? "border-cyan/30 bg-cyan/15 text-cyan"
                    : "border-white/10 bg-white/5 text-slate-300 hover:bg-white/10"
                )}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
