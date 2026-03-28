import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-2xl border text-sm font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan/70 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default:
          "border-cyan/20 bg-cyan/15 text-cyan shadow-glow hover:bg-cyan/20",
        secondary:
          "border-white/10 bg-white/5 text-slate-100 hover:bg-white/10",
        ghost:
          "border-transparent bg-transparent text-slate-200 hover:border-white/10 hover:bg-white/5",
        critical:
          "border-critical/40 bg-critical/15 text-rose-100 shadow-urgent hover:bg-critical/20"
      },
      size: {
        default: "h-11 px-4 py-2",
        sm: "h-9 rounded-xl px-3",
        lg: "h-12 rounded-2xl px-5 text-base",
        icon: "h-11 w-11"
      }
    },
    defaultVariants: {
      variant: "default",
      size: "default"
    }
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
      className={cn(buttonVariants({ variant, size, className }))}
      ref={ref}
      {...props}
      />
    );
  }
);
Button.displayName = "Button";

export { Button, buttonVariants };
