"use client";

import * as SwitchPrimitives from "@radix-ui/react-switch";

import { cn } from "@/lib/utils";

export function Switch({
  className,
  ...props
}: SwitchPrimitives.SwitchProps) {
  return (
    <SwitchPrimitives.Root
      className={cn(
        "peer inline-flex h-7 w-12 shrink-0 cursor-pointer items-center rounded-full border border-white/10 bg-white/10 px-1 transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan/70 data-[state=checked]:bg-cyan/35",
        className
      )}
      {...props}
    >
      <SwitchPrimitives.Thumb className="block h-5 w-5 rounded-full bg-white shadow transition data-[state=checked]:translate-x-5" />
    </SwitchPrimitives.Root>
  );
}

